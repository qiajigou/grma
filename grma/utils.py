import os

try:
    from os import closerange
except ImportError:
    def closerange(fd_low, fd_high):
        for fd in range(fd_low, fd_high):
            try:
                os.close(fd)
            except OSError:
                pass

try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        return


def getcwd():
    try:
        pwd = os.stat(os.environ['PWD'])
        cwd = os.stat(os.getcwd())
        if pwd.st_ino == cwd.st_ino and pwd.st_dev == cwd.st_dev:
            cwd = os.environ['PWD']
        else:
            cwd = os.getcwd()
    except:
        cwd = os.getcwd()
    return cwd


def daemonize():
    if os.fork():
        os._exit(0)
    os.setsid()

    if os.fork():
        os._exit(0)

    os.umask(0o22)

    closerange(0, 3)

    redir = getattr(os, 'devnull', '/dev/null')
    fd_null = os.open(redir, os.O_RDWR)

    if fd_null != 0:
        os.dup2(fd_null, 0)

    os.dup2(fd_null, 1)
    os.dup2(fd_null, 2)
