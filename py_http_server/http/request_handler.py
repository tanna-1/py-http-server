from ..networking.address import TCPAddress
from ..http.request import HTTPRequest
from ..http.response import HTTPResponse
from abc import ABC, abstractmethod


class RequestHandler(ABC):
    @abstractmethod
    def __call__(self, requester: TCPAddress, request: HTTPRequest) -> HTTPResponse: ...
