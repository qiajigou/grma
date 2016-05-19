import sys
import utils
import importlib

from config import Config
from mayue import Mayue


class Application(object):
    def __init__(self):
        self.cfg = None
        self.args = None
        self.server = None
        self.init_path()
        self.init_config()
        self.load_config()
        self.load_class()

    def __repr__(self):
        return '<Application>'

    def run(self):
        if self.server:
            Mayue(self).run()

    def init_path(self):
        path = utils.getcwd()
        sys.path.insert(0, path)

    def init_config(self):
        self.cfg = Config()

    def load_config(self):
        parser = self.cfg.parser()
        args = parser.parse_args()
        self.args = args

    def load_class(self):
        try:
            kls = self.args.cls
            module, var = kls.split(':')
            i = importlib.import_module(module)
            c = i.__dict__.get(var)
            if c:
                try:
                    if getattr(c, 'start') and getattr(c, 'stop'):
                        self.server = c
                except AttributeError:
                    msg = '''--cls={cls} have no [start] or [stop] method:

exp:

class App(object):
    def __init__(self):
        pass

    def start(self):
        # start the gRPC server

    def stop(self):
        # stop the gRPC server
                    '''
                    print msg
                    return False
            else:
                return False
        except Exception, e:
            print e
            return False


def run():
    Application().run()


if __name__ == '__main__':
    run()
