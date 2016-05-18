import argparse


class Config(object):
    def parser(self):
        parser = argparse.ArgumentParser(description='Run Server on PORT')
        parser.add_argument('--port', type=int, nargs='*',
                            default=8001,
                            help='an integer for gRPC Server port')
        parser.add_argument('--cls', type=str, required=True,
                            help='a string of gRPC server module '
                            '[app:server]')
        parser.add_argument('--num', type=int, default=1,
                            help='a string of gRPC server module ')

        return parser
