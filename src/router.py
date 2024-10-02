from http11.request import HTTPRequest
from http11.response import HTTPResponse
from networking.address import TCPAddress
from abc import ABC
from typing import Callable
import json
import logging

LOG = logging.getLogger("router")


class Router(ABC):
    def handle(self, requester: TCPAddress, request: HTTPRequest) -> HTTPResponse: ...


RouteHandler = Callable[[Router, TCPAddress, HTTPRequest], HTTPResponse]


def route(path):
    def _route_decorator(function):
        function._route = {"path": path}
        return function

    return _route_decorator


class DefaultRouter(Router):
    def __init__(self) -> None:
        super().__init__()

        # Define default headers
        self.default_headers = {
            "Content-Type": "text/html; charset=utf-8",
            "X-Powered-By": "Tan's HTTP Server",
        }  # type: dict[str, str]

        # Discover @route methods
        self.__handlers = {}  # type: dict[str, RouteHandler]
        for member in dir(self):
            value = getattr(self, member)
            if callable(value) and "_route" in dir(value):
                path = value._route["path"]
                LOG.debug(f'Discovered handler {value.__qualname__} for "{path}"')
                self.__handlers[path] = value

    def handle(self, requester: TCPAddress, request: HTTPRequest) -> HTTPResponse:
        if request.path in self.__handlers:
            # A handler was found.

            handler = self.__handlers[request.path]
            try:
                LOG.debug(
                    f'Calling handler {handler.__qualname__} for path "{request.path}"'
                )
                resp = handler(requester, request)  # type: HTTPResponse
            except Exception as exc:
                LOG.exception(
                    f'Exception in handler for path "{request.path}"', exc_info=exc
                )
                return self.internal_error_page(requester, request)

            # Set header values to default if unset
            new_headers = resp.headers
            for key, value in self.default_headers.items():
                if key not in new_headers:
                    new_headers[key] = value

            # HTTPResponse is immutable
            return HTTPResponse(resp.status_code, new_headers, resp.body)
        return self.not_found_page(requester, request)

    def internal_error_page(
        self, requester: TCPAddress, request: HTTPRequest
    ) -> HTTPResponse:
        return HTTPResponse(500, self.default_headers, b"500 Internal Server Error")

    def not_found_page(
        self, requester: TCPAddress, request: HTTPRequest
    ) -> HTTPResponse:
        return HTTPResponse(404, self.default_headers, b"404 Not Found")


class DebugRouter(DefaultRouter):
    @route("/json")
    def json_page(self, requester: TCPAddress, request: HTTPRequest) -> HTTPResponse:
        content = {
            "requester": str(requester),
            "request": {
                "headers": request.headers,
                "path": request.path,
                "query": request.query,
                "method": request.method,
                "version": request.version,
                "body": request.body.decode("ascii", "ignore"),
            },
        }

        return HTTPResponse(
            200,
            {"Content-Type": "application/json; charset=utf-8"},
            json.dumps(content).encode("utf-8"),
        )

    @route("/")
    def root_page(self, requester: TCPAddress, request: HTTPRequest) -> HTTPResponse:
        content = f'<!DOCTYPE html><html><body><a href="/json">Try the /json page</a>'
        content += f"<h3>Source Address</h3><p>{requester}</p>"
        content += f"<h3>Request Path</h3><p>{request.path}</p>"
        content += f"<h3>Request Query</h3><p>{request.query}</p>"
        content += f"<h3>Request Method</h3><p>{request.method}</p>"
        content += "<h3>Request Headers</h3><ul>"
        for key, value in request.headers.items():
            content += f"<li>{key}: {value}</li>"
        content += "</ul></body></html>"

        return HTTPResponse(200, body=content.encode("utf-8"))

    @route("/error")
    def error_page(self, requester: TCPAddress, request: HTTPRequest) -> HTTPResponse:
        raise RuntimeError("DebugRouter test exception")
