from http11.request import HTTPRequest
from http11.response import HTTPResponse, HTTP_STATUS_CODES
from networking.address import TCPAddress
from typing import Any, Callable, final
from json import dumps as json_dumps


class Router:
    def __init__(self, default_headers: dict[str, str | int] = {}):
        super().__init__()
        self.default_headers = default_headers

    # Convenience method
    @final
    @staticmethod
    def json(json: dict, headers: dict[str, str | int] = {}) -> HTTPResponse:
        return HTTPResponse(
            200,
            headers | {"Content-Type": "application/json; charset=utf-8"},
            json_dumps(json).encode("utf-8"),
        )

    # Convenience method
    @final
    @staticmethod
    def html(html: str, headers: dict[str, str | int] = {}) -> HTTPResponse:
        return HTTPResponse(
            200,
            headers | {"Content-Type": "text/html; charset=utf-8"},
            html.encode("utf-8"),
        )

    # Convenience method
    @final
    @staticmethod
    def status(status_code: int, headers: dict[str, str | int] = {}) -> HTTPResponse:
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
        return HTTPResponse(status_code, headers)

    # Do not override
    @final
    def __call__(self, requester: TCPAddress, request: HTTPRequest) -> HTTPResponse:
        resp = self._handle(requester, request)

        # Build a status response if int is returned
        if isinstance(resp, int):
            resp = self.status(resp)

        # Set header values to default values if unset
        for key in self.default_headers:
            if key not in resp.headers:
                resp.headers[key] = self.default_headers[key]
        return resp

    # Override this
    def _handle(
        self, requester: TCPAddress, request: HTTPRequest
    ) -> HTTPResponse | int:
        raise NotImplementedError()


RouteHandler = Callable[[TCPAddress, HTTPRequest], HTTPResponse | int]
