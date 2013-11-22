from django.core.management.commands.runfcgi import Command as RunFcgiCommand

# This is enhanced RunFcgiCommand
# which handles proctitle= and user= params
class Command(RunFcgiCommand):
    def handle(self, *args, **options):
        for arg in args:
            if arg.startswith('proctitle='):
                from setproctitle import setproctitle
                setproctitle(arg[len('proctitle='):])
            if arg.startswith('user='):
                from os import setuid, setgid
                from pwd import getpwnam
                pw = getpwnam(arg[len('user='):])
                setgid(pw.pw_gid)
                setuid(pw.pw_uid)
        RunFcgiCommand.handle(self, *args, **options)
