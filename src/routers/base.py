from http11.request import HTTPRequest
from http11.response import HTTPResponse
from networking.address import TCPAddress
from abc import ABC
from typing import Callable


class Router(ABC):
    def handle(self, requester: TCPAddress, request: HTTPRequest) -> HTTPResponse: ...


RouteHandler = Callable[[TCPAddress, HTTPRequest], HTTPResponse]
