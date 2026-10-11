import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from dockerfile_lint.cli import main
from dockerfile_lint.core import lint, parse


def codes(text):
    return {f.code for f in lint(text)}


class ParseTests(unittest.TestCase):
    def test_continuations_join_into_one_instruction(self):
        ins = parse("RUN a \\\n  && b\nCMD x\n")
        self.assertEqual([i.keyword for i in ins], ["RUN", "CMD"])
        self.assertIn("&& b", ins[0].args)

    def test_comments_and_blank_lines_skipped(self):
        self.assertEqual(len(parse("# c\n\nFROM x\n")), 1)


class RuleTests(unittest.TestCase):
    def test_latest_and_untagged_images(self):
        self.assertIn("DL001", codes("FROM ubuntu:latest\nUSER a\n"))
        self.assertIn("DL001", codes("FROM ubuntu\nUSER a\n"))
        self.assertNotIn("DL001", codes("FROM ubuntu:22.04\nUSER a\n"))
        self.assertNotIn("DL001", codes("FROM ubuntu@sha256:abc\nUSER a\n"))

    def test_registry_port_is_not_a_tag(self):
        self.assertIn("DL001", codes("FROM registry.local:5000/app\nUSER a\n"))

    def test_missing_user_warns_on_final_stage(self):
        self.assertIn("DL002", codes("FROM python:3.12\nCMD x\n"))
        self.assertNotIn("DL002", codes("FROM python:3.12\nUSER app\n"))

    def test_add_local_vs_remote(self):
        self.assertIn("DL003", codes("FROM x:1\nADD app.py /app/\nUSER a\n"))
        self.assertNotIn("DL003", codes("FROM x:1\nADD app.tar.gz /opt/\nUSER a\n"))
        self.assertNotIn("DL003", codes("FROM x:1\nADD https://example.com/f /tmp/\nUSER a\n"))

    def test_secret_env_is_error_but_empty_is_not(self):
        self.assertIn("DL008", codes("FROM x:1\nENV API_TOKEN=abc\nUSER a\n"))
        self.assertNotIn("DL008", codes("FROM x:1\nENV API_TOKEN=\nUSER a\n"))
        self.assertNotIn("DL008", codes("FROM x:1\nENV DEBUG=true\nUSER a\n"))

    def test_curl_pipe_shell_is_error(self):
        self.assertIn("DL007", codes("FROM x:1\nRUN curl -fsSL https://e.com/i.sh | sh\nUSER a\n"))
        self.assertNotIn("DL007", codes("FROM x:1\nRUN curl -o f https://e.com/i.sh\nUSER a\n"))

    def test_apt_rules(self):
        c = codes("FROM x:1\nRUN apt-get install -y git\nUSER a\n")
        self.assertIn("DL004", c)
        self.assertIn("DL005", c)
        good = codes("FROM x:1\nRUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*\nUSER a\n")
        self.assertNotIn("DL005", good)

    def test_multiple_cmd(self):
        self.assertIn("DL009", codes("FROM x:1\nUSER a\nCMD a\nCMD b\n"))

    def test_no_from_is_error(self):
        self.assertIn("DL000", codes("RUN echo hi\n"))

    def test_examples_behave_as_documented(self):
        good = Path("examples/good.Dockerfile").read_text(encoding="utf-8")
        bad = Path("examples/bad.Dockerfile").read_text(encoding="utf-8")
        self.assertEqual([f for f in lint(good) if f.level != "info"], [])
        self.assertTrue(any(f.level == "error" for f in lint(bad)))


class CliTests(unittest.TestCase):
    def run_cli(self, argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main(argv)
        return code, buf.getvalue()

    def test_good_file_exit_zero_and_bad_exit_one(self):
        tmp = Path(tempfile.mkdtemp())
        good = tmp / "Dockerfile"
        good.write_text("FROM x:1.2\nUSER a\nHEALTHCHECK CMD true\nCMD x\n", encoding="utf-8")
        self.assertEqual(self.run_cli([str(good)])[0], 0)
        bad = tmp / "bad"
        bad.write_text("FROM x\nENV PASSWORD=1\n", encoding="utf-8")
        self.assertEqual(self.run_cli([str(bad)])[0], 1)

    def test_strict_turns_warning_into_failure(self):
        tmp = Path(tempfile.mkdtemp())
        f = tmp / "Dockerfile"
        f.write_text("FROM x:1.2\nUSER a\nCMD x\nCMD y\n", encoding="utf-8")
        self.assertEqual(self.run_cli([str(f)])[0], 0)
        self.assertEqual(self.run_cli(["--strict", str(f)])[0], 1)

    def test_missing_file_exit_two(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.run_cli(["/no/Dockerfile"])[0], 2)

    def test_json(self):
        tmp = Path(tempfile.mkdtemp())
        f = tmp / "Dockerfile"
        f.write_text("FROM x:1.2\nUSER a\nCMD x\n", encoding="utf-8")
        code, out = self.run_cli(["--json", str(f)])
        self.assertIn(str(f), json.loads(out))


if __name__ == "__main__":
    unittest.main()
