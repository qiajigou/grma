import os
import sys
import utils
import signal

from time import sleep

from grma import __version__, __logo__
from worker import Worker
from pidfile import Pidfile


class Mayue(object):
    ctx = dict()
    workers = dict()

    def __init__(self, app):
        self.app = app
        self.pid = None
        self.pidfile = None
        self.try_to_stop = False

        args = sys.argv[:]
        args.insert(0, sys.executable)
        cwd = utils.getcwd()

        self.ctx = dict(args=args, cwd=cwd, exectable=sys.executable)

    def spawn_worker(self):
        sleep(0.1)
        worker = Worker(self.pid, self.app.server, self.app.args)

        pid = os.fork()

        if pid != 0:
            # parent process
            self.workers[pid] = worker
            return pid

        # child process
        try:
            worker.run()
            sys.exit(0)
        except Exception as e:
            print e
        finally:
            worker.stop()

    def stop_workers(self):
        for pid, worker in self.workers.items():
            worker.stop()
            del self.workers[pid]
            self.kill_worker(pid, signal.SIGKILL)

    def kill_worker(self, pid, sig):
        try:
            os.kill(pid, sig)
        except OSError:
            pass

    def clean(self):
        self.stop_workers()
        if self.pidfile is not None:
            self.pidfile.unlink()

    def run(self):
        print __logo__

        print '[OK] Running grma {version}'.format(version=__version__)

        print '-' * 10 + ' CONFIG ' + '-' * 10

        cf = dict()
        for arg in vars(self.app.args):
            cf[arg] = getattr(self.app.args, arg)

        for k, v in cf.items():
            msg = '{key}\t{value}'.format(key=k, value=v)
            print msg

        print '-' * 28

        if self.app.args.daemon:
            utils.daemonize()

        self.pid = os.getpid()

        self.app.server.bind(
            self.app.args.host, self.app.args.port,
            self.app.args.private, self.app.args.certificate
            )

        print '[OK] Master running pid: {pid}'.format(pid=self.pid)
        utils.setproctitle('grma master pid={pid}'.format(pid=self.pid))

        for i in range(self.app.args.num):
            self.spawn_worker()

        if self.app.args.pid:
            self.pidfile = Pidfile(self.app.args.pid)
            self.pidfile.create(self.pid)

        self.init_signals()

        while True:
            try:
                sleep(1)
                if self.try_to_stop:
                    break
            except:
                self.clean()
                break
        # gRPC master server should close first
        self.kill_worker(self.pid, signal.SIGKILL)

    def init_signals(self):
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGQUIT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)

    def handle_exit(self, sig, frame):
        self.clean()
        self.try_to_stop = True
