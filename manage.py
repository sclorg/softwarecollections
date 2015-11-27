#!/usr/bin/env python3
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "softwarecollections.settings")

    if os.getuid() == 0 and 'collectstatic' not in sys.argv:
        from django.conf import settings
        import pwd, grp
        user = pwd.getpwnam('softwarecollections')
        groups = [g.gr_gid for g in grp.getgrall() if user.pw_name in g.gr_mem]
        os.setgid(user.pw_gid)
        os.setgroups(groups)
        os.setuid(user.pw_uid)
        os.environ['USER']      = user.pw_name
        os.environ['LOGNAME']   = user.pw_name
        os.environ['HOME']      = user.pw_dir
        os.environ['SHELL']     = user.pw_shell
        os.chdir(os.environ['HOME'])

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
