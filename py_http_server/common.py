from .networking.address import TCPAddress
from .http.request import HTTPRequest
from .http.response import HTTPResponse
from abc import ABC, abstractmethod
from typing import Union
import os


class RequestHandler(ABC):
    @abstractmethod
    def __call__(
        self, requester: TCPAddress, request: "HTTPRequest"
    ) -> HTTPResponse: ...


PathLike = Union[str, bytes, os.PathLike]
