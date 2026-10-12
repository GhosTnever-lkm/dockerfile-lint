# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.2] - 2026-10-13

### Added

- Parse `FROM --platform` options before checking base image tags.
- Detect secrets in both modern `ENV KEY=value` and legacy `ENV KEY value` syntax.
- Add CLI version regression coverage, install guidance, badges, and tagged wheel/sdist releases with SHA-256 checksums.

### Fixed

- Avoid missing `:latest` warnings when a `FROM` alias uses mixed case.
- Treat only a valid SHA-256 digest as a pinned image.
- Do not flag empty secret assignments with trailing comments.

## [0.1.1] - 2026-10-11

### Added

- CI now also runs the test suite on Windows (windows-latest), not only Ubuntu.
- `--ignore CODE` (repeatable) to skip specific rules, for example `DL010`.


## [0.1.0] - 2026-10-11

### Added

- Rules DL000–DL010: missing FROM, unpinned or `:latest` base images, root user, `ADD` for local files, apt and pip hygiene, `curl | sh`, secrets in ENV/ARG, duplicate CMD/ENTRYPOINT, missing HEALTHCHECK.
- `--strict` and `--json` modes; exit code 2 for unreadable files.

[Unreleased]: https://github.com/GhosTnever-lkm/dockerfile-lint/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/GhosTnever-lkm/dockerfile-lint/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/GhosTnever-lkm/dockerfile-lint/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/GhosTnever-lkm/dockerfile-lint/releases/tag/v0.1.0
