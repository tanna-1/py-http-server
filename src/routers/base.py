from http11.response import HTTPResponseFactory
from http11.request_handler import RequestHandler


class Router(RequestHandler):
    def __init__(self, response_factory=HTTPResponseFactory()):
        self.http = response_factory
