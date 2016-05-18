import os
import utils


class Worker(object):
    def __init__(self, server, args):
        self.server = server
        self.args = args

    def run(self):
        pid = os.getpid()
        print '[OK] Worker running with pid: {pid}'.format(pid=pid)
        if self.args.daemon:
            utils.daemonize()
        self.server.start()

    def stop(self):
        self.server.stop()
