import os
import sys
import jobset
import signal
import subprocess

from time import sleep
from config import port, cpu_count

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
JEDI_PATH = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, JEDI_PATH)


class TouchQPSWorker(object):
    def __init__(self):
        self.cpu_count = cpu_count
        self.running = False

    def start(self):
        jobset.message('START', 'Start running worker background')
        prepare_jobs = []
        ports = [port + i for i in range(self.cpu_count)]
        for p in ports:
            exc = '%s/touch_test.py' % CURRENT_DIR
            prepare_jobs.append(
                (
                    [sys.executable, exc, '-P', str(p)],
                )
            )
        processes = []
        for job in prepare_jobs:
            servers = lambda: subprocess.Popen(job[0])
            process = servers()
            processes.append(process)
        self.processes = processes
        jobset.message('SUCCESS', 'Runing Worker [cores=%s]' % self.cpu_count)
        self.running = True

    def stop(self):
        jobset.message('START', 'Start shutdown subprocess')
        for p in self.processes:
            try:
                p.terminate()
                p.wait()
                try:
                    os.killpg(p.pid, signal.SIGTERM)
                except OSError:
                    pass
            except:
                pass
        self.running = False
        jobset.message('SUCCESS', 'Done', do_newline=True)


worker = TouchQPSWorker()


def signal_handler(signal, frame):
    worker.stop()

# signal.signal(signal.SIGINT, signal_handler)
# signal.signal(signal.SIGQUIT, signal_handler)
# signal.signal(signal.SIGTERM, signal_handler)
# signal.signal(signal.SIGCHLD, signal_handler)


if __name__ == '__main__':
    worker.start()
    while worker.running:
        try:
            sleep(1)
        except KeyboardInterrupt:
            sys.exit(1)
