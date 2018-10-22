#!/usr/bin/env python3
"""Manage softwarecollections instance.

Can be installed and run as management binary for deployment.
"""

import grp
import os
import pwd
import sys
from collections import deque
from itertools import filterfalse
from operator import methodcaller
from pathlib import Path
from warnings import warn

from django.core.management import execute_from_command_line

#: Paths searched for environment file
ENV_PATHS = [Path.cwd() / ".env", Path("/etc/sysconfig/softwarecollections.env")]
#: Commands which are allowed to be run as root
ALLOW_ROOT = {"collectstatic"}
#: Minimal environment necessary for successful execution
MINIMAL_ENVIRONMENT = {
    "DJANGO_SETTINGS_MODULE": "softwarecollections.settings",
    "LANG": "C.utf-8",
    "LC_CTYPE": "C.utf-8",
}


def switch_user(name="softwarecollections"):
    """Change the current user to the specified one.

    Keyword arguments:
        name: The name (login) of the user to switch to.
        Must exists on the system.
    """

    user = pwd.getpwnam(name)
    groups = [g.gr_gid for g in grp.getgrall() if user.pw_name in g.gr_mem]

    # Execution context
    os.setgid(user.pw_gid)
    os.setgroups(groups)
    os.setuid(user.pw_uid)

    # Environment
    os.environ.update(
        USER=user.pw_name, LOGNAME=user.pw_name, HOME=user.pw_dir, SHELL=user.pw_shell
    )


def parse_env_file(file):
    """Parse environment file in similar way to SystemD unit file.

    Keyword arguments:
        file: The file-like object to parse.

    Returns:
        A dictionary with the parsed keys.
    """

    def is_comment(line):
        return line.startswith(("#", ";")) or "=" not in line

    def concat_lines(line_iter):
        """Concatenate backslash-ending lines"""

        buffer = deque()

        for line in line_iter:
            if line.endswith("\\"):
                buffer.append(line[:-1])
            else:
                buffer.append(line)
                yield "".join(buffer)
                buffer.clear()

    def strip(line):
        # First strip whitespace, then any double quotes
        return line.strip().strip('"')

    line_iter = map(methodcaller("rstrip", "\n"), file)
    line_iter = filter(None, line_iter)  # empty lines
    line_iter = filterfalse(is_comment, line_iter)
    line_iter = concat_lines(line_iter)

    split_iter = map(methodcaller("partition", "="), line_iter)

    return {key: strip(value) for key, _sep, value in split_iter}


def load_env_file(candidate_path_list=ENV_PATHS):
    """Load configuration from environment file.

    Keyword arguments:
        candidate_path_list: List of paths to try to read configuration from;
            first readable will be used.
            If none exists, a warning will be issued.
    """

    for candidate in candidate_path_list:
        if os.access(candidate, os.R_OK):
            configuration = candidate
            break
    else:
        warn("No readable environment file found; using default configuration.")
        return

    with configuration.open(encoding="utf-8") as file:
        os.environ.update(parse_env_file(file))


if __name__ == "__main__":
    for envvar, value in MINIMAL_ENVIRONMENT.items():
        os.environ.setdefault(envvar, value)

    subcommand = sys.argv[1] if len(sys.argv) >= 2 else None
    if os.getuid() == 0 and subcommand not in ALLOW_ROOT:
        switch_user()

    if Path(sys.argv[0]).name != "manage.py":
        load_env_file()

    execute_from_command_line(sys.argv)
