# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).


## [Unreleased]
### Fixed
- Avoid TypeError passing a `StaticContentNamedPipe` to `pass_fds` under uvloop

## [0.1.0] — 2024-01-04
### Added
- Expose report subcommand of vacuum to provide linting results in Pydantic models
