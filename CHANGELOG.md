# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.1] - 2023-03-21

### Fixed

- Discard existing intermediates when recompiling LaTeX source.

## [0.3.0] - 2023-03-21

### Changed

- `rr` implemenetation
  - Many cleanups in `__main__` (simpler and safer code, more reuse)
- Improvements to `rr-python-script`
  - Parallel executions of parameterized scripts.
  - Logging of script output, compatible with pytest.
  - Allow underscores in script names.
- Improvements to `rr-latex`: improved output and code cleanups.
- Minor cleanups after linting

### Fixed

- Add BibTeX files to the dynamic dependencies.
- Allow (and require) configuration of `latexmk` through `latexmkrc`.
- Fix printing of relevant part of pdflatex log.
- Load LaTeX log file as binary, because its encoding is unpredictable.
- Sort files inside ZIP to make their order reproducible.

## [0.2.0] - 2023-03-16

### Fixed

- Fixed other minor dependency tracking issues
- Fixed dependency issues for Latex files.
- Assume `SOURCE_DATE_EPOCH=315532800` (Jan 1, 1980) for compatibility with ZIP files.
- When writing a build.ninja file, change directory before importing a python script.

### Changed

- Alpha status
- Aim for Python 3.6
- All command-line arguments of `rr` and `rrr` are given to the `ninja` subprocess.

## [0.1.2] - 2023-03-15

### Added

- The main build command `rr` and its continuous equivalent `rrr`.
- Utilities that users do not need to interact with directly.
  (They are invoked by `rr` when appropriate.)
  - `rr-zip`: Create a reproducible zip file (timestamps fixed at 1980-01-01T00:00:00Z)
  - `rr-article-zip`: Create a reproducible zip file with all LaTeX inputs of an article.
  - `rr-latex`: Compile a reproducible PDF with LaTeX, including dependency tracking
  - `rr-python-script`: Execute a Python script, including dependency tracking.
  - `rr-normalize-pdf`: Remove irrelevant metadata and standardize a PDF file.
