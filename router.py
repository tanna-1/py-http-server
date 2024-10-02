from http11.request import HTTPRequest
from http11.response import HTTPResponse
from networking.address import TCPAddress
from abc import ABC


class Router(ABC):
    def handle(self, requester: TCPAddress, request: HTTPRequest) -> HTTPResponse: ...


class DebugRouter(Router):
    def handle(self, requester: TCPAddress, request: HTTPRequest) -> HTTPResponse:
        content = (
            f"<!DOCTYPE html><html><body><h3>Source Address</h3><p>{requester}</p>"
        )
        content += f"<h3>Request URL</h3><p>{request.url}</p>"
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
