#!/usr/bin/env python3
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "softwarecollections.settings")

    if os.getuid() == 0:
        import pwd
        apache = pwd.getpwnam('apache')
        os.setgid(apache.pw_gid)
        os.setuid(apache.pw_uid)
        os.environ['USER']  = apache.pw_name
        os.environ['HOME']  = apache.pw_dir
        os.environ['SHELL'] = apache.pw_shell
        os.chdir(os.environ['HOME'])

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
