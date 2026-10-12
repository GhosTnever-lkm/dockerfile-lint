"""Parse Dockerfile instructions (with line continuations) and apply rules. Read-only, offline."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

SECRET_KEY_RE = re.compile(r"(PASSWORD|PASSWD|SECRET|TOKEN|API_?KEY|PRIVATE_?KEY)", re.IGNORECASE)
CURL_PIPE_SHELL_RE = re.compile(r"(curl|wget)\b[^|;&]*\|\s*(sudo\s+)?(sh|bash|zsh)\b")
ADD_REMOTE_OR_ARCHIVE_RE = re.compile(r"^(https?://|git@|.*\.(tar|tar\.gz|tgz|tar\.xz|tar\.bz2|zip)$)", re.IGNORECASE)


@dataclass(frozen=True)
class Instruction:
    line: int
    keyword: str
    args: str


@dataclass(frozen=True)
class Finding:
    level: str  # error | warning | info
    code: str
    line: int
    message: str


def parse(text: str) -> list[Instruction]:
    instructions: list[Instruction] = []
    buffer = ""
    start = 0
    for number, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not buffer and (not stripped or stripped.startswith("#")):
            continue
        if not buffer:
            start = number
        if stripped.endswith("\\"):
            buffer += stripped[:-1].rstrip() + " "
            continue
        buffer += stripped
        keyword, _, args = buffer.strip().partition(" ")
        instructions.append(Instruction(start, keyword.upper(), args.strip()))
        buffer = ""
    if buffer.strip():
        keyword, _, args = buffer.strip().partition(" ")
        instructions.append(Instruction(start, keyword.upper(), args.strip()))
    return instructions


def lint(text: str) -> list[Finding]:
    ins = parse(text)
    findings: list[Finding] = []
    add = lambda level, code, line, msg: findings.append(Finding(level, code, line, msg))  # noqa: E731

    stages = [i for i in ins if i.keyword == "FROM"]
    if not stages:
        add("error", "DL000", 1, "no FROM instruction found")
        return findings

    for i in stages:
        image = _from_image(i.args)
        if not image:
            continue
        if image.lower() == "scratch":
            continue
        if "@" in image:
            if re.search(r"@sha256:[0-9a-f]{64}$", image, re.IGNORECASE):
                continue
            add("warning", "DL001", i.line, f"base image {image!r} does not use a valid pinned sha256 digest")
            continue
        name, tag = (image.rsplit(":", 1) if ":" in image.rsplit("/", 1)[-1] else (image, ""))
        if tag in ("", "latest"):
            add("warning", "DL001", i.line, f"base image {image!r} is unpinned or uses :latest")

    last_stage_start = max(idx for idx, i in enumerate(ins) if i.keyword == "FROM")
    if not any(i.keyword == "USER" for i in ins[last_stage_start:]):
        add("warning", "DL002", ins[last_stage_start].line, "final stage has no USER instruction; the container runs as root")

    for i in ins:
        if i.keyword == "ADD":
            sources = i.args.split()[:-1] if "--" not in i.args[:2] else i.args.split()[1:-1]
            if sources and not all(ADD_REMOTE_OR_ARCHIVE_RE.match(s) for s in sources):
                add("warning", "DL003", i.line, "ADD copies local files; use COPY unless auto-extraction is needed")
        if i.keyword in ("ENV", "ARG"):
            for key, value in _environment_pairs(i.args, i.keyword):
                value = re.split(r"\s+#", value, maxsplit=1)[0].strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                    value = value[1:-1]
                if SECRET_KEY_RE.search(key) and value:
                    add("error", "DL008", i.line, f"{i.keyword} {key} looks like a secret stored in the image")
        if i.keyword == "RUN":
            if CURL_PIPE_SHELL_RE.search(i.args):
                add("error", "DL007", i.line, "RUN pipes a remote download into a shell")
            if re.search(r"\bapt-get\s+install\b", i.args):
                if "--no-install-recommends" not in i.args:
                    add("info", "DL004", i.line, "apt-get install without --no-install-recommends")
                if "rm -rf /var/lib/apt/lists" not in i.args:
                    add("warning", "DL005", i.line, "apt-get install without cleaning /var/lib/apt/lists in the same layer")
            if re.search(r"\bpip\s+install\b", i.args) and "--no-cache-dir" not in i.args:
                add("info", "DL006", i.line, "pip install without --no-cache-dir")

    for keyword in ("CMD", "ENTRYPOINT"):
        count = [i for i in ins[last_stage_start:] if i.keyword == keyword]
        if len(count) > 1:
            add("warning", "DL009", count[1].line, f"multiple {keyword} in the final stage; only the last one takes effect")

    if not any(i.keyword == "HEALTHCHECK" for i in ins[last_stage_start:]):
        add("info", "DL010", ins[last_stage_start].line, "no HEALTHCHECK in the final stage")

    return findings


def _from_image(args: str) -> str:
    tokens = args.split()
    index = 0
    while index < len(tokens) and tokens[index].startswith("--"):
        option = tokens[index]
        index += 1
        if "=" not in option and index < len(tokens) and not tokens[index].startswith("--"):
            index += 1
    return tokens[index] if index < len(tokens) else ""


def _environment_pairs(args: str, keyword: str) -> list[tuple[str, str]]:
    tokens = args.split()
    if not tokens:
        return []
    if keyword == "ENV" and "=" not in tokens[0]:
        return [(tokens[0], " ".join(tokens[1:]))] if len(tokens) > 1 else []
    pairs = []
    for token in tokens:
        key, separator, value = token.partition("=")
        if separator:
            pairs.append((key, value))
    return pairs


def lint_file(path: str | Path) -> list[Finding]:
    return lint(Path(path).read_text(encoding="utf-8", errors="replace"))
