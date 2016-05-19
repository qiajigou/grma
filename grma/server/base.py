class ServerBase(object):
    """All gRPC server class should base on"""

    def __repr__(self):
        return '<%s>' % self.__class__.__name__

    def start(self):
        raise NotImplementedError()

    def bind(self, host, port, private_key_path='', certificate_chain_path=''):
        raise NotImplementedError()

    def stop(self, grace=0):
        raise NotImplementedError()
