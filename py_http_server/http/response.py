from ..http.constants import STATUS_CODES
from typing import Any, Optional, Union, Literal, cast
from pathlib import Path
import socket
import json


class ResponseBody:
    def __init__(self, content: Union[bytes, Path]):
        self.content = content

    def __len__(self):
        return self.__len

    @property
    def content(self) -> Union[bytes, Path]:
        return self.__content

    @content.setter
    def content(self, value: Union[bytes, Path]):
        if isinstance(value, bytes):
            self.__type = "bytes"
            self.__len = len(value)
        elif isinstance(value, Path):
            self.__type = "file"
            self.__len = value.stat().st_size
        else:
            raise ValueError("Unknown content type")
        self.__content = value

    @property
    def type(self) -> Literal["file", "bytes"]:
        return self.__type # type: ignore

    def send_to(self, conn: socket.socket):
        if self.type == "bytes":
            self.content = cast(bytes, self.content)
            conn.send(self.content)
        elif self.type == "file":
            self.content = cast(Path, self.content)
            with self.content.open("rb") as f:
                conn.sendfile(f)


HeadersType = dict[str, str]


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

    @property
    def body_file(self):
        return self.__body_file

    @body_file.setter
    def body_file(self, value: Optional[str]):
        self.__body_file = value

    def send_to(self, conn: socket.socket, http_version: str):
        if self.body:
            self.__headers["Content-Length"] = str(len(self.body))
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
            ResponseBody(json.dumps(value).encode(encoding)),
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
            ResponseBody(value.encode(encoding)),
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
                ResponseBody(STATUS_CODES[status_code].encode(encoding)),
            )

        # Status code is not allowed to have a body or is unknown
        return HTTPResponse(status_code, headers)
