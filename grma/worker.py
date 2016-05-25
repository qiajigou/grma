import os
import utils
import signal
import logging


class Worker(object):
    logger = logging.getLogger(__name__)

    def __init__(self, pid, server, args):
        self.server = server
        self.args = args
        self.master_pid = pid

    def init_worker(self):
        self.init_signals()

    def run(self):
        pid = os.getpid()
        self.logger.info('[OK] Worker running with pid: {pid}'.format(pid=pid))
        utils.setproctitle('grma worker pid={pid}'.format(pid=pid))
        self.server.start()

    def stop(self):
        self.server.stop(self.args.grace)

    def init_signals(self):
        signal.signal(signal.SIGQUIT, self.handle_quit)
        signal.signal(signal.SIGTERM, self.handle_exit)
        signal.signal(signal.SIGINT, self.handle_quit)

    def _stop(self):
        self.stop()

    def handle_quit(self, sig, frame):
        self._stop()

    def handle_exit(self, sig, frame):
        self._stop()
