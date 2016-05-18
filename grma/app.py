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
                self.server = c
            else:
                raise
        except:
            raise


def run():
    Application().run()


if __name__ == '__main__':
    run()
