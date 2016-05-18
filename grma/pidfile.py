# original code from gunicorn pidfile
# has some little change

import errno
import os
import tempfile


class Pidfile(object):
    def __init__(self, fname):
        self.fname = fname
        self.pid = None

    def create(self, pid):
        oldpid = self.validate()
        if oldpid:
            if oldpid == os.getpid():
                return
            msg = ('Already running on PID {oldpid} '
                   '(or pid file {fname} is stale)')
            raise RuntimeError(msg.format(oldpid=oldpid, fname=self.fname))
            raise RuntimeError(msg % (oldpid, self.fname))

        self.pid = pid

        # Write pidfile
        fdir = os.path.dirname(self.fname)
        if fdir and not os.path.isdir(fdir):
            msg = '{fdir} does not exitst, cant create pidfile'.format(
                fdir=fdir)
            raise RuntimeError(msg)
        fd, fname = tempfile.mkstemp(dir=fdir)
        os.write(fd, ('{pid}\n'.format(pid=self.pid)).encode('utf-8'))
        if self.fname:
            os.rename(fname, self.fname)
        else:
            self.fname = fname
        os.close(fd)
        os.chmod(self.fname, 420)

    def rename(self, path):
        self.unlink()
        self.fname = path
        self.create(self.pid)

    def unlink(self):
        try:
            with open(self.fname, 'r') as f:
                pid1 = int(f.read() or 0)

            if pid1 == self.pid:
                os.unlink(self.fname)
        except:
            pass

    def validate(self):
        if not self.fname:
            return
        try:
            with open(self.fname, 'r') as f:
                try:
                    wpid = int(f.read())
                except ValueError:
                    return

                try:
                    os.kill(wpid, 0)
                    return wpid
                except OSError as e:
                    if e.args[0] == errno.ESRCH:
                        return
                    raise
        except IOError as e:
            if e.args[0] == errno.ENOENT:
                return
            raise
