# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]

## [1.12.0] - 2024-01-30

### Changed

- The `inp` field now accepts more general named wildcards:
  Not all named wildcards need to exist in the first input argument.
  Some or all may appear later.
  For example, the following is now supported:

  ```yaml
  - command: copy
    inp: foo-${*suffix}/file.txt foo-${*suffix}/case-${*num}.txt
    out: out-${*suffix}-${*num}/
  ```

  This will create `copy` build steps in `build.ninja` for every combination of `suffix` and `num`,
  for which files exist.
  Previously, the second input file had to be placed first, which is not always convenient.
  (For the copy example, the order is not relevant.)

### Added

- Commands accept a `default: false` option to run the corresponding builds only when needed by
  other builds. This replaces the underscore prefix of the command, which still works.
- Commands accept an `optional: true` option to raise no error in case of missing inputs for the
  command.


## [1.11.1] - 2024-01-22

### Fixed

- Raise a `ValueError` when some named wildcards exist for the first input but not for the latter ones.
  This is usually due to a typo, so an error message is in order.


## [1.11.0] - 2024-01-21

### Fixed

- Detect images included in SVG files as implicit dependencies.
- Improve LaTeX Error summary by running it in errorstopmode.

### Changed

- Phony option was removed from build commands.
- Imports are no longer inherited through the `subdir` command.
  (This reduces correlation between different `reprepbuild.yaml` files, making them more robust.)
- Make `rr-latex` less verbose unless the aux file does not converge.
- The `viarables` section is removed from `reprepbuild.yaml`.
  Instead, constants can be defined in JSON files and through environment variables:
  - `REPREPBUILD_ROOT` can be set to the top-level directory containing a `reprepbuild.yaml` in
    hierarchical projects. The default value is the current working directory.
  - `REPREPBUILD_CONSTANTS` can be a list of colon-separated JSON files defining constants.
    The default value is `${REPREPBUILD_ROOT}/constants.json`.
  - When build commands or scripts need these variables, the JSON files must be listed as input files.
    Only the commands `rr`, `rrr` and `rr-generator` will pick up the environment variables mentioned above.
    They only use these variables for writing the `build.ninja` file and will not pass them on to other scripts.


### Added

- Added support for fine-grained control of LaTeX dependencies, to handle non-standard cases:
  - A line starting with `%REPREPBUILD input` followed by a filename, will add that filename to the
    implicit inputs for the latex compilation.
  - A line containing `%REPREPBUILD ignore` will not be analyzed when scanning for implicit inputs.
- Add `built_inputs_only` option to build commands.
  When `True`, only previous outputs are considered as potential inputs.
  When `False` (default), also files on disk are considered.


## [1.10.1] - 2024-01-07

### Fixed

- Fixed broken progress bar when using the "barrier" task.
- Improved the clarity of the progress bar by truncating long descriptions.
- Do not add `mkdir` to a phony rule.
- Fix typo in `python_script` command.
- Add missing informative comments to build.ninja to facilitate debugging.
- More informative error messages.

## [1.10.0] - 2024-01-05

### Fixed

- Only consider other tex files as dependencies for latex_flat (not figures).
- Fixed failure to identify error message in blg file.
- Improved detection of required LaTeX recompilation (sha256 of aux file).

### Changed

- Add option for maximum number of LaTeX recompilations to get references right.

### Added

- Conversion from PDF to PNG with `convert_pdf_png`.


## [1.9.2] - 2024-01-03

### Fixed

- Ignore UTF-8 decoding errors when reading LaTeX log files
  These files have no predictable encoding and they are only used to print out a summarized
  error message, for which ignoring a garbled character does not hurt.
- After rewriting build.ninja, ninja is informed of the updated build.ninja,
  so it never starts by immediately regenerating it again.
- Remove transient outputs from previous LaTeX builds before calling `(pdf|xe|lua)latex`.
  This prevents irrelevant LaTeX failures in rare corner cases.
- Show progress bar when generator takes more than one second.
- Improve efficiency of `script_driver`.


## [1.9.1] - 2023-12-27

### Fixed

- Fixed failure to detect reasons to recompile the LaTeX source once more.


## [1.9.0] - 2023-12-26

### Fixed

- Potential cyclic dependency bug in `zip_plain`.

### Changed

- Undo separation of `latex` and `latex_bibtex` from version 1.8.0,
  and make distinction with a `skip_bibtex` optional argument.
  This restores backward compatibility.


## [1.8.0] - 2023-12-24 (yanked)

### Fixed

- LaTeX does not always produce a .out file (only when using hyperref),
  and it was therefore removed from the implicit outputs.

### Changed

- Separate `latex` and `latex_bibtex` to allow for more fine-grained control,
  e.g. to build LaTeX documents with fixed bbl file.

### Added

- The function `reprepbuild_cases` can have a variables argument.
- Add support for simple shell scripts in the workflow.
- A Python script driver, which can be used as generic main function.
  Add the following to Python scripts in the workflow:

```python
from reprepbuild import script_driver

...

if __name__ == "__main__":
    script_driver(__file__)
```

## [1.7.2] - 2023-12-07

### Fixed

- Correctly report missing `\bibstyle` command when BibTeX fails.
- Improve clarity of LaTeX and BibTeX error log processing.
- Corrected NameSpace attribute in `reprepbuild.scripts.manifest`.


## [1.7.1] - 2023-12-01

### Fixed

- Switch back to `fitz_new` API of PyMuPDF and constrain version to PyMuPDF>=1.23.7.
- Fix more edge cases in the detection of files referenced from a LaTeX source.


## [1.7.0] - 2023-11-30

### Added

- `rr-zip-plain` command to make ZIP files without prior `MANIFEST.in` file.
- Optionally provide `variables` argument to `reprepbuild_info`.

### Fixed

- Constrain PyMuPDF version due to [pymupdf/PyMuPDF#2815](https://github.com/pymupdf/PyMuPDF/issues/2815)
  **TODO:** This solution is still not ideal because it may occasionally result in segfaults.
- Fixed bug in the detection of files referenced from a LaTeX source.

### Changed

- The command `rr-zip` was renamed to `rr-zip-manifest`
- Some zip-related build rules were renamed:
  - `repro_zip` -> `zip_manifest`
  - `repro_zip_latex` -> `zip_latex`


## [1.6.2] - 2023-11-19

### Fixed

- Use fitz_new when available to work around the following issue: [pymupdf/PyMuPDF#2815](https://github.com/pymupdf/PyMuPDF/issues/2815)
- More informative error messages when writing `build.ninja`.


## [1.6.1] - 2023-11-17

### Fixed

- Fix missing `here` variables in render command.
- Fixed `reprepbuild.__version__`.


## [1.6.0] - 2023-11-15

### Added

- A new `hshift` optional argument for `layout_sub_figures` in `reprepbuild.helpers`
  can be used to tweak the placement of subfigure labels.


### Fixed

- Labels were not shown on subfigures (reason unclear).
  The function `layout_sub_figures` now uses the `TextWriter` API of PyMuPDF,
  which seems to work better.


## [1.5.0] - 2023-10-30

### Changed

- More customization features:
  - A more specific build config can precede a more general one,
    where the latter also defines build outputs of the former.
    In this case, the preceding command will get priority and no duplicate
    build outputs are written to `build.ninja`.
  - Each command in `reprepbuild.yaml` now also accepts an `override`
    field, to override variables locally.
    These overrides are only used when writing `build.ninja`.
    and are not included in `.reprepbuild/variables.json`.

### Fixed

- Fix for the LaTeX log parser.
  In some cases, the wrong the LaTeX source file was identified.


## [1.4.2] - 2023-10-09

### Fixed

- Regenerate `ninja.build` when files change from which dependencies were derived.
  Previously, it would only be regenerated when missing files were created,
  which is insufficient.


## [1.4.1] - 2023-10-05

### Fixed

- Ignore ID (`#`) in URLs in the script `rr-check-hrefs`.


## [1.4.0] - 2023-10-04

### Added

- Script to convert Markdown to HTML and PDF, with KaTeX support: `rr-markdown-pdf`.
  (Corresponding build rules are also included, only for PDF.)

### Changed

- More sensible variable, module and script names.
  To facilitate extensibility, `latex_zip` is renamed `zip_latex`.
  Other name changes are more internal.

### Fixed

- Fix for the LaTeX log parser.
  In some cases, the wrong the LaTeX source file was identified.


## [1.3.0] - 2023-10-02

### Changed

- Add `--ignore` options to `rr-check-hrefs`.
- Extend `arg` of `check_hrefs` in `reprepbuild.yaml` to be a dictionary with
  optional `translate` and `ignore` arguments passed on to `rr-check-hrefs`.

### Fixed

- Fix detection if relevant part of LaTeX log for the case `! LaTeX Error: Something's wrong`
- Fix several issues with `rr-check-hrefs`.
- Minor cleanups


## [1.2.0] - 2023-09-25

### Added

- Add the `relpath` Jinja2 filter to the ``rr-render``.
- Add option to configure DPI to `pdf_raster`.
- Added `barrier` feature to postpone later builds until all previous ones have completed.
  This is useful for checks that require all (preceding) outputs to be present.
- New `--translate` option for `rr-check-hrefs` to translate remote URLs to local paths.

### Changed

- More intuitive names for some classes and modules.

### Fixed

- Send output of `gs` in command `pdf_raster` to `/dev/null.
- Pass `variables` to `Command.generate` method to support more complicated build lines.
- Place `convert_odf_pdf` and `convert_svg_pdf` into their respective pools with depth 1,
  as a workaround for concurrency issues.
- Minor cleanups.
- When relevant, the (random) PDF trailer ID is removed in the scripts `rr-pdf-add-notes`,
  `rr-pdf-normalize` and `rr-pdf-nup`.


## [1.1.0] - 2023-09-21

### Added

- Introduced (or restored to some extent) `rr-latex` script to handle LaTeX and BibTex.
  A Python script makes it easier to handle more corner cases and
  to provide opportunity to keep improving the error detection in future versions.
- Call [bibsane](https://github.com/reproducible-reporting/bibsane) again,
  as in pre-1.0.0 versions.
- Colored output

### Fixed

- Set `SOURCE_DATE_EPOCH` as late as possible, inside `rr-latex` and `rr-python-script` to
  make sure this variable is set in all scenarios.
- Perform variable substitution in pre-defined variables defined in `reprepbuild.builtin`.


## [1.0.0] - 2023-09-19

This is an API-breaking release with lots of refactoring.
For users, the main change is that `reprepbuild.yaml` configuration file must be added.
In most cases, the example file from the [templates](https://github.com/reproducible-reporting/templates)
repository is just fine.

### Added

- New script `rr-generator`, which just writes the `build.ninja` file without calling `ninja`.
- Conversion of Open Document files to to `.pdf`.
- Rendering of source files (e.g. LaTeX or Markdown) with Jinja2, with `rr-render`.
- Paths of external tools (like `inkscape`, `pdflatex`, ...) are configurable.
- A rule for merging PDFs with `mutool`: `pdf_merge`.
- A rule for rastering PDFs with `gs`: `pdf_raser`.
- A script for inserting notes pages: `rr-pdf-add-notes`,
  with corresponding command `pdf_add_notes`.
- A script for generating handouts: `rr-pdf-nup`,
  with corresponding command `pdf_nup`.
- A script for checking hyper references: `rr-check-hrefs`,
  with with corresponding command `check_hrefs`.

### Changed

- Tasks are no longer deduced from file patterns alone.
  They have to be defined in a new file `reprepbuild.yaml`.
  This config file makes `RepRepBuild` much more broadly applicable.
- Autogenerated TeX files can just end with `.tex`, so `.itex` is no longer needed.
- LaTeX dependencies are detected by grepping for `\input`, `\import` and `\includegraphics`.
  It is assumed that the filenames can be interpreted without having to compile the LaTeX source.
  The special `\warninput` command is no longer needed.
- No longer using Ninja's dynamic dependencies, using `generator=1` instead to regenerate the
  `build.ninja` when new files were created that may change the dependency graph.
- Dependency files and outputs of Python scripts are hidden (prefixed with a dot).
- Output directories are created when not present yet.

### Fixed

- Autogenerated LaTeX sources may also contain `\input`, `\import` and `\includegraphics`.
  It's even ok when these also refer to tex files that have to be generated in previous steps.
- Specify `SOURCE_DATE_EPOCH` in `build.ninja`, as to make sure the variable is set correctly.

### Removed

- A few scripts are no longer needed and have been removed: `rr-latex`, `rr-latex-dep`, `rr-bibtex`.
- The special `\warninput` LaTeX command is no longer needed.
  Use ordinary `\input` instead.


## [0.13.3] - 2023-09-13

### Fixed

- Catch and print exceptions in `write_ninja` function in `rrr` command.


## [0.13.2] - 2023-08-09

### Fixed

- Fix dependency for `latexflat` once more.


## [0.13.1] - 2023-08-09

### Fixed

- Fix dependency for `latexflat`.


## [0.13.0] - 2023-08-09

### Changed

- Before calling latexdiff, the LaTeX source is flattened with `rr-latexflat`, which correctly
  handles the `\warninput` command, unlike `latexdiff --flatten`.


## [0.12.1] - 2023-08-02

### Fixed

- Fix dependency for `latexdiff`.


## [0.12.0] - 2023-08-02

### Fixed

- Allow `*-diff.tex` build output.

### Changed

- Assume old version for `latexdiff` resides in `old` sub directory,
  instead of relying on `*-old.tex` suffix.
  `latexdiff --flatten` is always used, which makes the diff work for sources distributed
  over multiple tex files.


## [0.11.0] - 2023-07-07

### Added

- Helper functions for templating with jinja and combining PDFs into one figure.
- Utility script `rr-manifest` to convert a `MANIFEST.in` into a `MANIFEST.sha256`.

### Changed

- More efficient ZIP: copy file before checking hash and compression to reduce
  network load on remote datasets.
- No build lines are added when the required inputs come from datasets that are not present.
  In this case, it is recommended that the owner of the dataset commits the results of such
  builds to the Git repository, so those without access to the dataset can still complete the build.
- The `glob` call used to find all relevant build tasks for `build.ninja` is no longer recursive,
  to avoid that this becomes a bottleneck in case of data sets with a huge number of files.
- In the `rrr` command, watchdogs are only installed on the current directory and its
  subdirectories, without deeper recursions, for the same reason as in the previous point.
- Use script prefix in log files (and others) when `REPREPBUILD_CASE_FMT` is not specified.


## [0.10.1] - 2023-06-27

### Fixed

- Convert SVG to PDF with text to path conversion. This reduces the risk of font issues.


## [0.10.0] - 2023-06-23

### Changed

- The script `rr-zip` now takes a `MANIFEST.sha256` file as second argument with the complete
  file list. This change is introduced for two reasons.
  (1) Very long file lists are allowed, even longer than what is supported by shell commands.
  (2) An additional check is introduced to make sure the ZIP file contains the right files,
  i.e. the same as when the SHA256 sums were created.


## [0.9.1] - 2023-06-21

### Fixed

- Print out BibTeX error messages from the correct `.blg` file.


## [0.9.0] - 2023-06-16

### Changed

- The variable `REPREPBUILD_CASE_FMT` is no longer prefixed with the script name
  to create filenames for log and dependency files.
  Instead, it is used as such, without prefixing anything to it.
- A plain `dataset` directory is now also recognized and turned into a ZIP file.


## [0.8.0] - 2023-05-26

### Fixed

- Added sanity check to `rrr` command.

### Changed

- Optional customization of formatting and parsing of script arguments when using
  `reprepbuild_cases`.


## [0.7.4] - 2023-05-15

### Fixed

- Make local imports of Python scripts work when executed through RepRepBuild.


## [0.7.3] - 2023-05-10

### Fixed

- Also detect bare `results` folder without suffix.


## [0.7.2] - 2023-04-27

### Fixed

- Support for upper case in Python scripts and SVG files.
- Ignore Python scripts that cannot be imported.
  When this happens, a comment is added to `build.ninja`.


## [0.7.1] - 2023-04-19

### Fixed

- Enfore a different extension than `.tex` for autogenerated LaTeX sources
  to break circular dependencies.
- Fix mistakes in depfile for Python scripts.


## [0.7.0] - 2023-04-17

### Fixed

- Add option to latexdiff to track changes in other common sections in articles.

### Changed

- Also ZIP the supporting information sources, which is needed in some scenario's,
  such as submission of a preprint to arXiv.


## [0.6.0] - 2023-04-12

### Fixed

- Add option to latexdiff to track changes in the abstract when it is in the preamble.

### Changed

- Run bibsane directly after bibtex, using the configuration file `bibsane.yaml` located
  next to the `build.ninja` file.


## [0.5.1] - 2023-04-11

### Fixed

- Get latexdiff to work.


## [0.5.0] - 2023-03-30

### Fixed

- Use regular deflation algorithm for a more acceptable ZIP compression time.
- Allow for more filename patterns when assigning build rules.

### Changed

- When the compression of the ZIP file takes more than 1 second, a progress bar appears.
  This introduces a dependency on [`tqdm`](https://github.com/tqdm/tqdm).


## [0.4.2] - 2023-03-25

### Fixed

- Fix typo in `rr-bibtex` script.


## [0.4.1] - 2023-03-25

### Fixed

- Add missing depfile lines to `latexdep` and `bibtex` build rules.
- Let the build fail when `bibtex` finds no `.bib` file.


## [0.4.0] - 2023-03-24

### Changed

- The LaTeX sources no longer built without `latexmk`.
  It is replaced by a set of build commands in the `build.ninja` file generated by rr.
  A few extra scripts were added to make this all work: `rr-latexdep` and `rr-bibtex`.
- When LaTeX makes an emergency stop, which is not compatible with RepRepBuild,
  `rr-latexdep` will explain how to solve this problem.

### Fixed

- Fixed compression of ZIP files.
- The regular expression has been updated to be more permissive and now matches Python files with numbers in their name.
- Fix minor typos and update the regular expression for function arguments to allow for strings containing both letters and numbers to be valid function arguments.


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
