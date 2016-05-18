import os


class Worker(object):
    def __init__(self, server):
        self.server = server

    def run(self):
        pid = os.getpid()
        print '[OK] Worker running with pid: {pid}'.format(pid=pid)
        self.server.start()

    def stop(self):
        self.server.stop()
