from http11.request import HTTPRequest
from http11.response import HTTPResponse
from networking.address import TCPAddress
from abc import ABC
import json


class Router(ABC):
    def handle(self, requester: TCPAddress, request: HTTPRequest) -> HTTPResponse: ...


class DebugRouter(Router):
    def handle(self, requester: TCPAddress, request: HTTPRequest) -> HTTPResponse:
        if request.path in self.HANDLERS:
            return self.HANDLERS[request.path](self, requester, request)

        return HTTPResponse(
            404,
            {
                "Content-Type": "text/html; charset=utf-8",
                "X-Powered-By": "Tan's HTTP Server",
            },
            "404 Not Found".encode("utf-8"),
        )

    def json_page(self, requester: TCPAddress, request: HTTPRequest) -> HTTPResponse:
        content = {
            "requester": str(requester),
            "request": {
                "headers": request.headers,
                "path": request.path,
                "method": request.method,
                "version": request.version,
                "body_ascii": request.body.decode("ascii", "ignore"),
            },
        }

        return HTTPResponse(
            200,
            {
                "Content-Type": "application/json; charset=utf-8",
                "X-Powered-By": "Tan's HTTP Server",
            },
            json.dumps(content).encode("utf-8"),
        )

    def root_page(self, requester: TCPAddress, request: HTTPRequest) -> HTTPResponse:
        content = f'<!DOCTYPE html><html><body><a href="/json">Try the /json page</a>'
        content += f"<h3>Source Address</h3><p>{requester}</p>"
        content += f"<h3>Request URL</h3><p>{request.path}</p>"
        content += f"<h3>Request Method</h3><p>{request.method}</p>"
        content += "<h3>Request Headers</h3><ul>"
        for key, value in request.headers.items():
            content += f"<li>{key}: {value}</li>"
        content += "</ul></body></html>"

        return HTTPResponse(
            200,
            {
                "Content-Type": "text/html; charset=utf-8",
                "X-Powered-By": "Tan's HTTP Server",
            },
            content.encode("utf-8"),
        )

    HANDLERS = {"/": root_page, "/json": json_page}
