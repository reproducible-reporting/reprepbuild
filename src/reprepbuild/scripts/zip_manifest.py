# RepRepBuild is the build tool for Reproducible Reporting.
# Copyright (C) 2024 Toon Verstraelen
#
# This file is part of RepRepBuild.
#
# RepRepBuild is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# RepRepBuild is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
#
# --
"""Create reproducible zip files from a MANIFEST.in file."""


import argparse
import datetime
import os
import shutil
import sys
import tempfile
import zipfile

from tqdm import tqdm

from .manifest import compute_sha256

__all__ = ("make_zip_manifest",)


TIMESTAMP = datetime.datetime(1980, 1, 1).timestamp()


def main() -> int:
    """Main program."""
    args = parse_args()
    return make_zip_manifest(args.path_man, args.path_zip)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="rr-zip-manifest", description="Create a reproducible ZIP file."
    )
    parser.add_argument(
        "path_man",
        help="The MANIFEST.sha256 with all files to be zipped. "
        "The sha256 sums of the files will be checked before archiving. "
        "The manifest file will be included in the ZIP.",
    )
    parser.add_argument("path_zip", help="Destination zip file.")
    return parser.parse_args()


def make_zip_manifest(path_man: str, path_zip: str, check_sha256: bool = True) -> int:
    """Create a reproducible zip file."""
    if not path_zip.endswith(".zip"):
        print(f"Destination must have a `.zip` extension. Got {path_zip}")
        return 2
    if not path_man.endswith(".sha256"):
        print(f"Manifest file must have a `.sha256` extension. Got {path_man}")
        return 2

    root, paths_in = load_manifest(path_man)
    result = create_zip(path_zip, root, paths_in, check_sha256)
    if result != 0:
        os.remove(path_zip)
    return result


def load_manifest(path_man: str) -> tuple[str, dict[str, (int, str)]]:
    """Load a MANIFEST.sha256 file.

    Parameters
    ----------
    path_man
        The file to be loaded.

    Returns
    -------
    root
        The location of the MANIFEST.sha256 file.
    paths_in
        A dict whose keys are paths in the MANIFEST.sha256 file, relative to root.
        The values are tuples of the size (in bytes) and the sha256 hash.
    """
    root = os.path.dirname(path_man)
    with open(path_man) as f:
        lines = f.readlines()
    # Normalize the paths and store file info in dict
    paths_in = {path_man: None}
    for line in lines:
        size = int(line[:15])
        sha256 = line[16:80].lower()
        path = os.path.normpath(os.path.join(root, line[81:].strip()))
        paths_in[path] = (size, sha256)
    return root, paths_in


def create_zip(
    path_zip: str, root: str, paths_in: dict[str, (int, str)], check_sha256: bool
) -> int:
    """Create the reproducible ZIP file.

    Parameters
    ----------
    path_zip
        The ZIP file to be created.
    root
        The root directory of the contents for the ZIP file.
    paths_in
        A dict whose keys are paths, relative to root.
        The values are tuples of the size (in bytes) and the sha256 hash.
    check_sha256
        When True, the file will be validated with size and hash
        before adding it to the ZIP file.
        In case of a mismatch, the partial ZIP is removed.

    Return
    ------
    exitcode
        The exit code of the script.
    """
    # Remove old zip
    if os.path.isfile(path_zip):
        os.remove(path_zip)

    # Create new one.
    nskip = 0 if root == "" else len(root) + 1
    with tempfile.TemporaryDirectory("rr-zip") as tmpdir:
        with zipfile.ZipFile(path_zip, "w") as fz:
            for src, info in tqdm(sorted(paths_in.items()), "Compressing", delay=1):
                # Copy the file to a temp dir.
                # This saves bandwith in case of remote datasets and allows
                # fixing the timestamp before compression.
                dst = os.path.join(tmpdir, "todo")
                shutil.copyfile(src, dst)
                os.utime(dst, (TIMESTAMP, TIMESTAMP))
                # Check if needed
                if check_sha256 and info is not None:
                    size, sha256 = info
                    mysize, mysha256 = compute_sha256(dst)
                    if size != mysize:
                        print(f"Size mismatch for file: got {mysize}, expected {size}, for {src}")
                        return 2
                    if sha256 != mysha256:
                        print(
                            "SHA256 mismatch for file: "
                            f"got {mysha256}, expected {sha256}, for {src}"
                        )
                        return 2
                # Compress
                fz.write(dst, src[nskip:], zipfile.ZIP_DEFLATED)
    return 0


if __name__ == "__main__":
    sys.exit(main())
