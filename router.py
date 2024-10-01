from http_request import HTTPRequest
from http_response import HTTPResponse
from abc import ABC
import ipaddress


class SourceAddress:
    def __init__(self, ip: str, port: int):
        if not isinstance(port, int) or port < 0 or port > 65535:
            raise ValueError("Invalid port")

        if not isinstance(ip, str) or not ip:
            raise ValueError("Invalid IP")

        self.__ipversion = ipaddress.ip_address(ip).version
        self.__ip = ip
        self.__port = port

    @property
    def ip(self) -> str:
        return self.__ip

    @property
    def port(self) -> int:
        return self.__port

    def __str__(self) -> str:
        if self.__ipversion == 6:
            return f"[{self.__ip}]:{self.__port}"
        return f"{self.__ip}:{self.__port}"


class Router(ABC):
    def handle(self, address: SourceAddress, request: HTTPRequest) -> HTTPResponse: ...


class DebugRouter(Router):
    def handle(self, address: SourceAddress, request: HTTPRequest) -> HTTPResponse:
        content = f"<!DOCTYPE html><html><body><h3>Source Address</h3><p>{address}</p>"
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
