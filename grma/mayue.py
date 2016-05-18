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

        args = sys.argv[:]
        args.insert(0, sys.executable)
        cwd = utils.getcwd()

        self.ctx = dict(args=args, cwd=cwd, exectable=sys.executable)

    def spawn_worker(self):
        sleep(0.1)
        worker = Worker(self.app.server)

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
        self.pid = os.getpid()
        self.init_signals()
        if self.app.args.pid:
            self.pidfile = Pidfile(self.app.args.pid)
            self.pidfile.create(self.pid)
        print __logo__
        print '[OK] Running grma {version}'.format(version=__version__)

        for i in range(self.app.args.num):
            self.spawn_worker()

        while True:
            try:
                sleep(1)
            except:
                self.clean()
                break
        self.kill_worker(self.pid, signal.SIGKILL)

    def init_signals(self):
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGQUIT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)
        signal.signal(signal.SIGCHLD, self.handle_exit)

    def handle_exit(self, sig, frame):
        self.clean()
        self.stop_workers()
        sys.exit(sig)
