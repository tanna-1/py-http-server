from abc import ABC, abstractmethod
from networking.address import TCPAddress
from http11.request import HTTPRequest
from http11.response import HTTPResponse


class RequestHandler(ABC):
    @abstractmethod
    def __call__(self, requester: TCPAddress, request: HTTPRequest) -> HTTPResponse: ...
