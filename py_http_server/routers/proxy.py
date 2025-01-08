from py_http_server.http.response_body import ResponseBody
from ..networking import ConnectionInfo
from ..http.request import HTTPRequest
from ..http.response import HTTPResponse, HTTPResponseFactory
from ..routers.base import Router
from urllib3 import PoolManager, BaseHTTPResponse
from urllib3.exceptions import HTTPError

ALLOWED_METHODS = [
    "GET",
    "POST",
    "PUT",
    "DELETE",
    "PATCH",
    "CONNECT",
    "OPTIONS",
    "TRACE",
]
IGNORED_REQUEST_HEADERS = ["host", "connection"]
IGNORED_RESPONSE_HEADERS = ["connection", "transfer-encoding"]


class ProxyRouter(Router):
    def __init__(
        self,
        proxy_host: str,
        add_x_forwarded: bool = False,
        stream_threshold=1048576,
        decode_content: bool = False,
    ):
        """Inits ProxyRouter.

        Args:
        proxy_host -- The base URL of the target server to proxy requests to.
        add_x_forwarded -- If True, adds X-Forwarded-For and X-Real-IP headers.
        stream_threshold -- Responses past this threshold will be streamed via chunked encoding.
        decode_content -- If True, decodes the response content based on the Content-Encoding header.
        """

        # Remove trailing slashes because the path will always start with /
        self.__proxy_host = proxy_host.rstrip("/")
        self.__add_x_forwarded = add_x_forwarded
        self.__stream_threshold = stream_threshold
        self.__decode_content = decode_content
        self.__pool = PoolManager()
        self.http = HTTPResponseFactory()

    def __call__(self, conn_info: ConnectionInfo, request: HTTPRequest) -> HTTPResponse:
        if request.method not in ALLOWED_METHODS:
            return self.http.status(405)

        url = f"{self.__proxy_host}{request.path}{request.query}"
        headers = self.__generate_request_headers(conn_info, request)

        # Forward the request
        try:
            response = self.__pool.request(
                method=request.method,
                url=url,
                body=request.body,
                headers=headers,
                preload_content=False,
                redirect=False,
                decode_content=self.__decode_content,
            )
            return self.__generate_response(response)
        except HTTPError:
            # 502 Bad Gateway
            return self.http.status(502)

    def __generate_request_headers(
        self, conn_info: ConnectionInfo, request: HTTPRequest
    ) -> dict:
        # Process request headers
        headers: dict[str, str] = {
            k: v
            for k, v in request.headers.items()
            if k.lower() not in IGNORED_REQUEST_HEADERS
        }

        # Add X-Forwarded-For and X-Real-IP headers if enabled
        if self.__add_x_forwarded:
            x_forwarded_for = request.headers.get("x-forwarded-for", "")
            if x_forwarded_for:
                headers["X-Forwarded-For"] = (
                    f"{conn_info.remote_address.ip}, {x_forwarded_for}"
                )
            else:
                headers["X-Forwarded-For"] = conn_info.remote_address.ip
            headers["X-Real-IP"] = conn_info.remote_address.ip

        return headers

    def __generate_response(self, response: BaseHTTPResponse) -> HTTPResponse:
        # Process response headers
        response_headers: dict[str, str] = {
            k: v
            for k, v in response.headers.items()
            if k.lower() not in IGNORED_RESPONSE_HEADERS
        }

        if self.__should_stream_response(response):
            return HTTPResponse(
                status_code=response.status,
                headers=response_headers,
                body=ResponseBody.from_stream(response),
            )
        else:
            return HTTPResponse(
                status_code=response.status,
                headers=response_headers,
                body=ResponseBody.from_bytes(response.data),
            )

    def __should_stream_response(self, response: BaseHTTPResponse) -> bool:
        # Stream responses if content size is above threshold or is unknown
        content_length = response.headers.get("Content-Length")
        try:
            return (
                content_length is None or int(content_length) > self.__stream_threshold
            )
        except ValueError:
            return True
