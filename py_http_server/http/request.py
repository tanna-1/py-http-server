from ..networking.connection_socket import ConnectionSocket
from .constants import HTTP_VERSIONS, HeadersType
import urllib.parse


class HTTPRequest:
    def __init__(
        self,
        method: str,
        raw_path: str,
        path: str,
        query: str,
        headers: HeadersType,
        version: str,
        body: bytes,
    ):
        self.method = method
        self.raw_path = raw_path
        self.path = path
        self.query = query
        self.version = version
        self.headers = headers
        self.body = body

    @property
    def method(self):
        return self.__method

    @method.setter
    def method(self, value: str):
        self.__method = value

    @property
    def raw_path(self):
        return self.__raw_path

    @raw_path.setter
    def raw_path(self, value: str):
        self.__raw_path = value

    @property
    def path(self):
        return self.__path

    @path.setter
    def path(self, value: str):
        self.__path = value

    @property
    def query(self):
        return self.__query

    @query.setter
    def query(self, value: str):
        self.__query = value

    @property
    def version(self):
        return self.__version

    @version.setter
    def version(self, value: str):
        self.__version = value.upper()

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
    def body(self, value: bytes):
        self.__body = value

    def to_url(self, host: str, schema: str):
        return f"{schema}://{host}{self.__raw_path}{self.__query}"

    def __str__(self):
        return f"{self.__method} {self.__raw_path}{self.__query} {self.__version}"

    @staticmethod
    def receive_from(
        conn: ConnectionSocket,
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
            method, raw_path, version = header_lines[0].split(" ")

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
        path = urllib.parse.unquote(raw_path)

        # Split the path to actual path and query, keeps the question mark
        path, qm, query = path.partition("?")
        query = qm + query

        return HTTPRequest(method, raw_path, path, query, headers, version, body)
