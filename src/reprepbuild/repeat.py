# RepRepBuild is the build tool for Reproducible Reporting.
# Copyright (C) 2023 Toon Verstraelen
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
"""Continuously repeat the RepRepBuild driver, using inotify events."""

import os
import subprocess
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .__main__ import DEFAULT_PATTERNS, DEFAULT_RULES, parse_args, write_ninja


class AnyChangeHandler(FileSystemEventHandler):
    """Report file changes in the current directory."""

    def __init__(self):
        self._changed = True
        self._watching = False

    @property
    def changed(self):
        """True when at least one file has changed."""
        return self._changed

    def reset(self):
        """Forget about changes and start watching again."""
        self._changed = False
        self._watching = True

    def snooze(self):
        """Stop watching."""
        self._watching = False

    def dispatch(self, event):
        """Process a file event."""
        # print(event)
        if not self._watching:
            return
        if event.is_directory:
            return
        if event.event_type in ["modified", "created"]:
            path = event.src_path
        elif event.event_type == "moved":
            path = event.dest_path
        else:
            return
        if os.path.basename(path).startswith("."):
            return
        print("  File changed:", path)
        self._changed = True


def main():
    """Main program."""
    args = parse_args()
    observer = Observer()
    event_handler = AnyChangeHandler()
    observer.schedule(event_handler, ".", True)
    observer.start()
    try:
        while True:
            if not event_handler.changed:
                time.sleep(1)
                continue
            event_handler.snooze()
            write_ninja(DEFAULT_PATTERNS, DEFAULT_RULES)
            subprocess.run(["ninja"] + args)
            time.sleep(0.1)
            event_handler.reset()
            print("  Waiting for new changes.")
    except KeyboardInterrupt:
        print("  See you!")
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    main()
