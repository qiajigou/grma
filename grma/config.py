import argparse


class Config(object):
    def parser(self):
        parser = argparse.ArgumentParser(description='A simple gunicorn like '
                                         'gRPC server management tool')
        parser.add_argument('--host', type=str,
                            default='0.0.0.0',
                            help='an string for gRPC Server host')
        parser.add_argument('--port', type=int,
                            default=60051,
                            help='an integer for gRPC Server port')
        parser.add_argument('--private', type=str, default='',
                            help='a string of private key path')
        parser.add_argument('--certificate', type=str, default='',
                            help='a string of private certificate key path')
        parser.add_argument('--cls', type=str, required=True,
                            help='a string of gRPC server module '
                            '[app:server]')
        parser.add_argument('--num', type=int, default=1,
                            help='a int of worker number')
        parser.add_argument('--pid', type=str,
                            help='pid file for grma')
        parser.add_argument('--daemon', type=int, default=0,
                            help='run as daemon')
        return parser
