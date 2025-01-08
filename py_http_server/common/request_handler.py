from ..networking import ConnectionInfo
from ..http.request import HTTPRequest
from ..http.response import HTTPResponse
from abc import ABC, abstractmethod


class RequestHandler(ABC):
    @abstractmethod
    def __call__(
        self, conn_info: ConnectionInfo, request: "HTTPRequest"
    ) -> HTTPResponse: ...
