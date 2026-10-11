# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.0] - 2026-10-11

### Added

- Rules DL000–DL010: missing FROM, unpinned or `:latest` base images, root user, `ADD` for local files, apt and pip hygiene, `curl | sh`, secrets in ENV/ARG, duplicate CMD/ENTRYPOINT, missing HEALTHCHECK.
- `--strict` and `--json` modes; exit code 2 for unreadable files.

[Unreleased]: https://github.com/GhosTnever-lkm/dockerfile-lint/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/GhosTnever-lkm/dockerfile-lint/releases/tag/v0.1.0
