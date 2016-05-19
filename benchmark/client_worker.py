import os
import sys
import signal
import jobset
import subprocess

from time import sleep

PATH = os.path.abspath(os.path.dirname(__file__))


class ClientWorker(object):
    def __init__(self):
        self.groups = []

    def register(self, args, process_num=1):
        jobset.message('START', '[%s] register %s' % (process_num, ' '.join(args)))
        id = len(self.groups) + 1
        info = dict(id=id, args=args, process_num=process_num)
        self.groups.append(info)
        jobset.message('SUCCESS', 'registed %s' % args)

    def spawn(self):
        for group in self.groups:
            try:
                process_num = group.get('process_num')
                args = group.get('args')
                _ps = []
                for i in range(process_num):
                    proc = subprocess.Popen(args, preexec_fn=os.setsid)
                    _ps.append(proc)
                group.update(proc_list=_ps)
            except Exception as e:
                jobset.message('FAIL', str(e))
                return

    def run(self):
        jobset.message('START', 'Start spawn subprocesses')
        self.spawn()
        while 1:
            sleep(1)


def signal_handler(sig, fra):
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGQUIT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGCHLD, signal_handler)

if __name__ == '__main__':
    jobset.message('START', 'start runnling client worker')
    try:
        r = ClientWorker()
        r.register(
            [sys.executable, PATH + '/touch_test.py'], 1
        )
        r.run()
    except Exception, e:
        jobset.message('FAIL', str(e))
        print e
    finally:
        jobset.message('SUCCESS', 'Done')
