from http11.request import HTTPRequest
from http11.response import HTTPResponse, HTTP_STATUS_CODES
from networking.address import TCPAddress
from abc import ABC
from typing import Callable


class Router(ABC):
    @staticmethod
    def status_response(
        status_code: int, headers: dict[str, str | int]
    ) -> HTTPResponse:
        if (
            status_code in HTTP_STATUS_CODES
            and status_code >= 200
            and status_code not in [204, 205, 304]
        ):
            # Set the body to the status code text
            return HTTPResponse(
                status_code,
                headers | {"Content-Type": "text/plain; charset=ascii"},
                HTTP_STATUS_CODES[status_code].encode("ascii"),
            )

        # Status code is not allowed to have a body or is unknown
        # Copy headers and delete Content-Type
        headers = dict(headers)
        if "Content-Type" in headers:
            del headers["Content-Type"]
        return HTTPResponse(status_code, headers)

    def handle(self, requester: TCPAddress, request: HTTPRequest) -> HTTPResponse: ...


RouteHandler = Callable[[TCPAddress, HTTPRequest], HTTPResponse]
