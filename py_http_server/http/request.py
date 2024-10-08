from .constants import HTTP_VERSIONS, HeadersType
import socket
import urllib.parse


class HTTPRequest:
    def __init__(
        self,
        method: str,
        path: str,
        query: str,
        headers: HeadersType,
        version: str,
        body: bytes,
    ):
        self.__method = method
        self.__path = path
        self.__query = query
        self.__version = version
        self.__headers = headers
        self.__body = body

    @property
    def method(self):
        return self.__method.upper()

    @property
    def path(self):
        return self.__path

    @property
    def query(self):
        return self.__query

    @property
    def version(self):
        return self.__version.upper()

    @property
    def headers(self):
        return self.__headers

    @property
    def body(self):
        return self.__body

    def __str__(self):
        return f"{self.__method} {self.__path}{self.__query} {self.__version}"

    @staticmethod
    def receive_from(
        conn: socket.socket,
        max_content_length: int = 10_000_000,
        max_header_size: int = 32768,
        recv_buffer_size: int = 32768,
    ):
        response = b""
        while b"\r\n\r\n" not in response:
            response += conn.recv(recv_buffer_size)
            if len(response) > max_header_size:
                raise ValueError("Header size exceeds maximum allowed length")
        headers_raw, _, body = response.partition(b"\r\n\r\n")

        try:
            header_lines = headers_raw.decode(encoding="ascii").split("\r\n")
            method, path, version = header_lines[0].split(" ")

            if version not in HTTP_VERSIONS:
                raise ValueError("Invalid HTTP version")

            headers: HeadersType = {}
            for line in header_lines[1:]:
                key, _, val = line.partition(":")
                headers[key.lower()] = val.strip()
        except (IndexError, ValueError, UnicodeDecodeError) as exc:
            raise ValueError(f"Request header is malformed. Inner {exc}")

        content_length = (
            int(headers["content-length"])
            if headers.get("content-length", "").isdigit()
            else None
        )

        if content_length:
            if content_length > max_content_length:
                raise ValueError("Content-Length is too large")
            while len(body) < content_length:
                body += conn.recv(min(recv_buffer_size, content_length - len(body)))

        # Parse percent encoding
        # Warning: This step is necessary to prevent unexpected vulnerabilities
        path = urllib.parse.unquote(path)

        # Split the path to actual path and query, keeps the question mark
        path, qm, query = path.partition("?")
        query = qm + query

        return HTTPRequest(method, path, query, headers, version, body)
