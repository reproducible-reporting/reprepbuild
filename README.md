[![PyPI Upload](https://github.com/reproducible-reporting/reprepbuild/actions/workflows/pypi.yaml/badge.svg)](https://github.com/reproducible-reporting/reprepbuild/actions/workflows/pypi.yaml)
[![pytest](https://github.com/reproducible-reporting/reprepbuild/actions/workflows/pytest.yaml/badge.svg)](https://github.com/reproducible-reporting/reprepbuild/actions/workflows/pytest.yaml)
[![PyPI Version](https://img.shields.io/pypi/v/reprepbuild)](https://pypi.org/project/reprepbuild/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/reprepbuild)
![GPL-3 License](https://img.shields.io/github/license/reproducible-reporting/reprepbuild)

# RepRepBuild

RepRepBuild is the build tool for [Reproducible Reporting](https://github.com/reproducible-reporting).
Run `rr` in a source directory, and the publication will be rebuilt from its source.

To get started, follow the [documentation](https://github.com/reproducible-reporting/templates/blob/main/DOCUMENTATION.md) of the [templates](https://github.com/reproducible-reporting/templates) repository.
RepRepBuild will be installed in your instance of the template, as part of the setup.

RepRepBuild emphasizes two kinds of reproducibility:

1. Byte-for-byte reproducibility of the generated files.
   If the same inputs are used, the same files are produced.
   Irrelevant timestamps and other annoyances are eliminated for this purpose.
2. Hands-free reproducible workflows for building publication files.
   Given the raw research results, anyone can regenerate
   plots, tables, and PDF files for a publication.

The first kind type of reproducibility helps with the second.
When a file changes in the Git commit history,
RepRepBuild tries to ensure that this is not the side effect of something irrelevant.
This makes it easier to trace the origin of (changes to) results.

If you would like to contribute, please read [CONTRIBUTING.md](https://github.com/reproducible-reporting/.github/blob/main/CONTRIBUTING.md).
