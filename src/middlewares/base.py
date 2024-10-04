from http11.response import HTTPResponseFactory
from http11.request_handler import RequestHandler


class Middleware(RequestHandler):
    def __init__(self, next: RequestHandler, response_factory=HTTPResponseFactory()):
        self.http = response_factory
        self.next = next
