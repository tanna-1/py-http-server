from http11.request import HTTPRequest
from http11.response import HTTPResponse, HTTPResponseFactory
from networking.address import TCPAddress
from typing import Callable, final

# Routers produce HTTPResponse
RouterResult = HTTPResponse


class Router:
    def __init__(self, response_factory: HTTPResponseFactory = HTTPResponseFactory()):
        super().__init__()
        self.resp_factory = response_factory

    # Do not override
    @final
    def __call__(self, requester: TCPAddress, request: HTTPRequest) -> RouterResult:
        resp = self._handle(requester, request)

        # Build a status response if int is returned
        if isinstance(resp, int):
            resp = self.resp_factory.status(resp)

        return resp

    # Override this
    def _handle(
        self, requester: TCPAddress, request: HTTPRequest
    ) -> RouterResult | int:
        raise NotImplementedError()


RouteHandler = Callable[[TCPAddress, HTTPRequest], HTTPResponse | int]
