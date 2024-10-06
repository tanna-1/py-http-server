from ..common import RequestHandler


class Middleware(RequestHandler):
    def __init__(self, next: RequestHandler):
        self.next = next
