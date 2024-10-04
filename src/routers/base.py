from http11.request import HTTPRequest
from http11.response import HTTPResponse, HTTPResponseFactory
from http11.request_handler import RequestHandler
from networking.address import TCPAddress
from typing import final


class Router(RequestHandler):
    def __init__(self, response_factory=HTTPResponseFactory()):
        self._httpf = response_factory

    # Do not override
    @final
    def __call__(self, requester: TCPAddress, request: HTTPRequest) -> HTTPResponse:
        resp = self._handle(requester, request)

        # Build a status response if int is returned
        if isinstance(resp, int):
            resp = self._httpf.status(resp)

        return resp

    # Override this
    def _handle(
        self, requester: TCPAddress, request: HTTPRequest
    ) -> HTTPResponse | int:
        raise NotImplementedError()
