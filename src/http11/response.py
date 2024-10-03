import socket
import json

HTTP_STATUS_CODES = {
    100: "Continue",
    101: "Switching Protocols",
    102: "Processing",
    200: "OK",
    201: "Created",
    202: "Accepted",
    203: "Non-Authoritative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    207: "Multi-Status",
    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    305: "Use Proxy",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Payload Too Large",
    414: "URI Too Long",
    415: "Unsupported Media Type",
    416: "Range Not Satisfiable",
    417: "Expectation Failed",
    418: "I'm a teapot",
    421: "Misdirected Request",
    422: "Unprocessable Entity",
    423: "Locked",
    424: "Failed Dependency",
    426: "Upgrade Required",
    428: "Precondition Required",
    429: "Too Many Requests",
    431: "Request Header Fields Too Large",
    451: "Unavailable For Legal Reasons",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
    505: "HTTP Version Not Supported",
    511: "Network Authentication Required",
}

HeadersType = dict[str, str | int]


class HTTPResponse:
    def __init__(
        self,
        status_code: int,
        headers: HeadersType = {},
        body: bytes = b"",
    ):
        self.__status_code = status_code
        self.__headers = headers
        if not isinstance(body, bytes):
            raise ValueError("Body must be of type bytes")
        self.__body = body

    @property
    def status_code(self) -> int:
        return self.__status_code

    @property
    def headers(self) -> HeadersType:
        return self.__headers

    @property
    def body(self) -> bytes:
        return self.__body

    def send_to(self, conn: socket.socket, http_version: str):
        self.__headers["Content-Length"] = len(self.__body)

        header_lines = "".join(
            f"{header}: {value}\r\n" for header, value in self.__headers.items()
        )

        status_code_str = str(self.__status_code)
        if self.__status_code in HTTP_STATUS_CODES:
            status_code_str += f" {HTTP_STATUS_CODES[self.__status_code]}"

        # Headers are always ASCII encoded
        response_header = (
            f"{http_version} {status_code_str}\r\n{header_lines}\r\n".encode("ascii")
        )

        # Send the HTTP header
        conn.send(response_header)

        if len(self.__body) > 0:
            conn.send(self.__body)


class HTTPResponseFactory:
    def __init__(
        self, default_headers: HeadersType = {}, default_encoding: str = "utf-8"
    ):
        self.default_headers = default_headers
        self.default_encoding = default_encoding

    def json(
        self,
        value: dict,
        status_code: int = 200,
        additional_headers: HeadersType = {},
        encoding: str | None = None,
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
            json.dumps(value).encode(encoding),
        )

    def html(
        self,
        value: str,
        status_code: int = 200,
        additional_headers: HeadersType = {},
        encoding: str | None = None,
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
            value.encode(encoding),
        )

    def status(
        self,
        status_code: int,
        additional_headers: HeadersType = {},
        encoding: str | None = None,
    ) -> HTTPResponse:
        encoding = encoding if encoding else self.default_encoding
        headers = self.default_headers | additional_headers

        if (
            status_code in HTTP_STATUS_CODES
            and status_code >= 200
            and status_code not in [204, 205, 304]
        ):
            # Set the body to the status code text
            return HTTPResponse(
                status_code,
                headers | {"Content-Type": f"text/plain; charset={encoding}"},
                HTTP_STATUS_CODES[status_code].encode(encoding),
            )

        # Status code is not allowed to have a body or is unknown
        return HTTPResponse(status_code, headers)
