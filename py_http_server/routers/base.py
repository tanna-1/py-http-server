from ..http.response import HTTPResponseFactory
from ..http.request_handler import RequestHandler


class Router(RequestHandler):
    def __init__(self, response_factory=HTTPResponseFactory()):
        self.http = response_factory
