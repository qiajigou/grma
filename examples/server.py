import time
import server_pb2

from grma.server.base import ServerBase

ONE_DAY_IN_SECONDS = 60 * 60 * 24


class ServiceImpl(server_pb2.BetaSimpleServiceServicer):
    def hello(self, request, context):
        say = request.say
        return server_pb2.HelloResponse(reply='you said: %s' % say)

    Hello = hello


class Server(ServerBase):
    def __init__(self):
        server = server_pb2.beta_create_SimpleService_server(
            ServiceImpl()
        )
        self.server = server
        self.started = False

    def bind(self, host, port, private_key_path='', certificate_chain_path=''):
        # return 0 if cannot binded
        r = self.server.add_insecure_port('%s:%s' % (host, port))
        return r

    def start(self):
        """start server"""
        self.server.start()
        self.started = True
        try:
            while self.started:
                time.sleep(ONE_DAY_IN_SECONDS)
        except KeyboardInterrupt:
            self.stop()

    def stop(self, grace=0):
        self.server.stop(0)
        self.started = False


# entry point of grma
app = Server()
