import os
import utils
import signal


class Worker(object):
    def __init__(self, pid, server, args):
        self.server = server
        self.args = args
        self.master_pid = pid
        self.init_signals()

    def run(self):
        pid = os.getpid()
        print '[OK] Worker running with pid: {pid}'.format(pid=pid)
        utils.setproctitle('grma worker pid={pid}'.format(pid=pid))
        self.server.start()

    def stop(self):
        self.server.stop()

    def init_signals(self):
        signal.signal(signal.SIGQUIT, self.handle_quit)
        signal.signal(signal.SIGTERM, self.handle_exit)
        signal.signal(signal.SIGINT, self.handle_quit)

    def _stop(self):
        self.stop()
        self.kill_worker(self.master_pid, signal.SIGTERM)

    def handle_quit(self, sig, frame):
        self._stop()

    def handle_exit(self, sig, frame):
        self._stop()

    def kill_worker(self, pid, sig):
        try:
            os.kill(pid, sig)
        except OSError:
            pass
