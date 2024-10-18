from ..networking.connection_socket import ConnectionSocket
from .constants import STATUS_CODES, HeadersType
from .response_body import ResponseBody
from typing import Any, Optional
import json


class HTTPResponse:
    def __init__(
        self,
        status_code: int,
        headers: HeadersType = {},
        body: Optional[ResponseBody] = None,
    ):
        self.status_code = status_code
        self.headers = headers
        self.body = body

    @property
    def status_code(self):
        return self.__status_code

    @status_code.setter
    def status_code(self, value: int):
        self.__status_code = value

    @property
    def headers(self):
        return self.__headers

    @headers.setter
    def headers(self, value: HeadersType):
        self.__headers = value

    @property
    def body(self):
        return self.__body

    @body.setter
    def body(self, value: Optional[ResponseBody]):
        self.__body = value

    def send_to(self, conn: ConnectionSocket, http_version: str):
        if self.body:
            self.__headers |= self.body.headers
        else:
            self.__headers["Content-Length"] = "0"

        header_lines = "".join(
            f"{header}: {value}\r\n" for header, value in self.__headers.items()
        )

        status_code_str = str(self.__status_code)
        if self.__status_code in STATUS_CODES:
            status_code_str += f" {STATUS_CODES[self.__status_code]}"

        # Headers are always ASCII encoded
        response_header = (
            f"{http_version} {status_code_str}\r\n{header_lines}\r\n".encode("ascii")
        )
        conn.send(response_header)

        if self.body:
            self.body.send_to(conn)
            
        # Optimize time-to-response
        conn.flush()


class HTTPResponseFactory:
    def __init__(
        self, default_headers: HeadersType = {}, default_encoding: str = "utf-8"
    ):
        self.default_headers = default_headers
        self.default_encoding = default_encoding

    def json(
        self,
        value: Any,
        status_code: int = 200,
        additional_headers: HeadersType = {},
        encoding: Optional[str] = None,
    ) -> HTTPResponse:
        encoding = encoding if encoding else self.default_encoding
        headers = (
            self.default_headers
            | additional_headers
            | {"Content-Type": f"application/json; charset={encoding}"}
        )

        return HTTPResponse(
            status_code,
            headers,
            ResponseBody.from_bytes(json.dumps(value).encode(encoding)),
        )

    def html(
        self,
        value: str,
        status_code: int = 200,
        additional_headers: HeadersType = {},
        encoding: Optional[str] = None,
    ) -> HTTPResponse:
        encoding = encoding if encoding else self.default_encoding
        headers = (
            self.default_headers
            | additional_headers
            | {"Content-Type": f"text/html; charset={encoding}"}
        )

        return HTTPResponse(
            status_code,
            headers,
            ResponseBody.from_bytes(value.encode(encoding)),
        )

    def status(
        self,
        status_code: int,
        additional_headers: HeadersType = {},
        encoding: Optional[str] = None,
    ) -> HTTPResponse:
        encoding = encoding if encoding else self.default_encoding
        headers = self.default_headers | additional_headers

        if (
            status_code in STATUS_CODES
            and status_code >= 200
            and status_code not in [204, 205, 304]
        ):
            # Set the body to the status code text
            return HTTPResponse(
                status_code,
                headers | {"Content-Type": f"text/plain; charset={encoding}"},
                ResponseBody.from_bytes(STATUS_CODES[status_code].encode(encoding)),
            )

        # Status code is not allowed to have a body or is unknown
        return HTTPResponse(status_code, headers)
