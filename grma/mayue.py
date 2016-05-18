import os
import sys
import utils
import signal

from time import sleep

from grma import __version__, __logo__
from worker import Worker


class Mayue(object):
    ctx = dict()
    workers = dict()

    def __init__(self, app):
        self.app = app
        self.pid = None

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
        self.kill_worker(self.pid, signal.SIGKILL)

    def kill_worker(self, pid, sig):
        try:
            os.kill(pid, sig)
        except OSError:
            pass

    def run(self):
        self.pid = os.getpid()
        print __logo__
        print '[OK] Running grma {version}'.format(version=__version__)

        for i in range(self.app.args.num):
            self.spawn_worker()

        while True:
            try:
                sleep(1)
            except:
                self.stop_workers()
                break
