import os
import sys
import utils
import signal
import errno
import select
import logging

from time import sleep

from grma import __version__, __logo__
from worker import Worker
from pidfile import Pidfile

_sigs = [getattr(signal, "SIG%s" % x)
         for x in "HUP QUIT INT TERM TTIN TTOU USR1 USR2 WINCH".split()]


class Mayue(object):
    ctx = dict()
    workers = dict()

    logger = logging.getLogger(__name__)
    pipe = list()
    signal_list = list()

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
            worker.init_worker()
            worker.run()
            sys.exit(0)
        except Exception as e:
            self.logger.exception('Exception: %s', e)
        finally:
            worker.stop()

    def spawn_workers(self):
        for i in range(self.app.args.num):
            self.spawn_worker()
        self.init_signals()

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
        host = self.app.args.host
        port = self.app.args.port

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

        binded = self.app.server.bind(
            host, port,
            self.app.args.private, self.app.args.certificate
            )

        if not binded:
            logging.info('[FAILED] Master cannot bind {host}:{port}, '
                         'or maybe bind function return None?'.format(
                             host=host, port=port))
            sys.exit(1)

        logging.info('[OK] Master running pid: {pid}'.format(pid=self.pid))
        utils.setproctitle('grma master pid={pid}'.format(pid=self.pid))

        self.init_signals()

        if self.app.args.pid:
            try:
                self.pidfile = Pidfile(self.app.args.pid)
                self.pidfile.create(self.pid)
            except:
                self.clean()
                sys.exit(1)

        self.manage_workers()
        while True:
            try:
                if self.try_to_stop:
                    break

                sig = self.signal_list.pop(0) if self.signal_list else None

                if sig is None:
                    self.sleep()
                    self.manage_workers()
                    continue

                self.process_signal(sig)
                self.wakeup()
            except KeyboardInterrupt:
                self.clean()
                break
            except Exception as e:
                self.logger.info(e)
                self.clean()
                break
        # gRPC master server should close first
        self.kill_worker(self.pid, signal.SIGKILL)

    def process_signal(self, sig):
        if not sig:
            return
        signame = utils.SIG_NAMES.get(sig)
        self.logger.info('Handing signal {signame}'.format(signame=signame))
        handler = getattr(self, "_handle_%s" % signame, None)
        if not handler:
            self.logger.error('no such a hander for sig {signame}'.format(
                signame=signame
            ))
        else:
            handler()

    def init_signals(self):

        if self.pipe:
            [os.close(p) for p in self.pipe]

        self.pipe = pair = os.pipe()

        for p in pair:
            utils.set_non_blocking(p)
            utils.close_on_exec(p)

        [signal.signal(s, self.handle_signal) for s in _sigs]
        signal.signal(signal.SIGCHLD, self._handle_chld)

    def handle_signal(self, sig, frame):
        if len(self.signal_list) < 10:
            self.signal_list.append(sig)
            self.wakeup()

    def wakeup(self):
        try:
            os.write(self.pipe[1], '.')
        except IOError as e:
            if e.errno not in [errno.EAGAIN, errno.EINTR]:
                raise

    def sleep(self):
        try:
            ready = select.select([self.pipe[0]], [], [], 1.0)
            if not ready[0]:
                return
            while os.read(self.pipe[0], 1):
                pass
        except select.error as e:
            if e.args[0] not in [errno.EAGAIN, errno.EINTR]:
                raise
        except OSError as e:
            if e.errno not in [errno.EAGAIN, errno.EINTR]:
                raise
        except KeyboardInterrupt:
            sys.exit()

    def stop(self):
        self.clean()
        self.try_to_stop = True

    def _handle_int(self):
        self.stop()

    def _handle_quite(self):
        self.stop()

    def _handle_term(self):
        self.stop()

    def _handle_chld(self, sig, frame):
        self.process_workers()
        self.wakeup()

    def process_workers(self):
        try:
            while True:
                wpid, status = os.waitpid(-1, os.WNOHANG)
                if not wpid:
                    break
                else:
                    worker = self.workers.pop(wpid, None)
                    if not worker:
                        continue
                    worker.stop()
        except OSError as e:
            if e.errno != errno.ECHILD:
                raise

    def manage_workers(self):
        diff = self.app.args.num - len(self.workers)
        if diff > 0:
            for i in range(diff):
                self.spawn_worker()

        workers = self.workers.items()
        while len(workers) > self.app.args.num:
            (pid, _) = workers.pop(0)
            self.kill_worker(pid, signal.SIGKILL)
