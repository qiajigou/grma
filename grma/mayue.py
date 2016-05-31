import os
import sys
import utils
import signal
import errno
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

    @property
    def num_workers(self):
        return self.app.args.num

    @num_workers.setter
    def num_workers(self, value):
        self.app.args.num = value

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
        for i in range(self.num_workers):
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
                    self.manage_workers()
                    continue

                self.process_signal(sig)
            except KeyboardInterrupt:
                self.clean()
                break
            except Exception as e:
                self.logger.exception(e)
                self.clean()
                break
        # gRPC master server should close first
        self.kill_worker(self.pid, signal.SIGKILL)

    def process_signal(self, sig):
        if not sig:
            return
        signame = utils.SIG_NAMES.get(sig)
        self.logger.info('Handing signal {signame}'.format(
            signame=signame.upper()))
        handler = getattr(self, "_handle_%s" % signame, None)
        if not handler:
            self.logger.error('no such a hander for sig {signame}'.format(
                signame=signame
            ))
        else:
            handler()

    def init_signals(self):
        [signal.signal(s, self.handle_signal) for s in _sigs]
        signal.signal(signal.SIGCHLD, self._handle_chld)

    def handle_signal(self, sig, frame):
        if len(self.signal_list) < 10:
            self.signal_list.append(sig)

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

    def _handle_ttin(self):
        """SIGTTIN handling.
        Increases the number of workers by one.
        """
        self.num_workers = self.num_workers + 1
        self.logger.info('Create a new worker. '
                         'Now you have {num} workers '
                         'work for you'.format(num=self.num_workers))
        self.manage_workers()

    def _handle_ttou(self):
        """SIGTTOU handling.
        Decreases the number of workers by one.
        """
        if self.num_workers <= 1:
            self.logger.error('You cannot kill the only worker you have.')
            return
        self.num_workers = self.num_workers - 1
        self.logger.info('Kill a worker. Now you have {num} workers '
                         'work for you'.format(num=self.num_workers))
        self.manage_workers()

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
        diff = self.num_workers - len(self.workers)
        if diff > 0:
            for i in range(diff):
                self.spawn_worker()

        workers = self.workers.items()
        while len(workers) > self.num_workers:
            (pid, _) = workers.pop(0)
            self.kill_worker(pid, signal.SIGKILL)
