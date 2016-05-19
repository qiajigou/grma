import argparse
import jobset
import time
import os

from config import cpu_count, total

from client import get_client


def run():
    pid = os.getpid()
    msg = str(pid)
    parser = argparse.ArgumentParser(description='Run Server on PORT')
    parser.add_argument('-P', metavar='P', type=int, nargs='+',
                        help='an integer for gRPC Server port')
    args = parser.parse_args()
    if args and args.P:
        port = args.P[-1]
        jobset.message('START', 'Run hello on port %s' % port, do_newline=True)
        c = get_client()
        start = time.time()
        tt = int(total / cpu_count)
        for i in range(tt):
            r = c.hello(msg)
            assert msg in str(r)
        end = time.time()
        diff = end - start
        qps = total / diff
        jobset.message('SUCCESS', 'Done hello total=%s, '
                       'time diff=%s, qps=%s' % (
                           total, diff, qps),
                       do_newline=True)

if __name__ == '__main__':
    run()
