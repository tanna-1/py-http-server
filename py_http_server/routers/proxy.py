from py_http_server.http.response_body import ResponseBody
from ..common import HeaderContainer, RequestHandler
from ..networking import ConnectionInfo
from ..http.request import HTTPRequest
from ..http.response import HTTPResponse, HTTPResponseFactory
from urllib3 import PoolManager, BaseHTTPResponse
from urllib3.exceptions import HTTPError

IGNORED_REQUEST_HEADERS = {"connection"}
IGNORED_RESPONSE_HEADERS = {"connection", "transfer-encoding"}


class ProxyRouter(RequestHandler):
    def __init__(
        self,
        proxy_host: str,
        stream_threshold: int = 1048576,
        add_forwarded_headers: bool = True,
        preserve_host: bool = False,
        decode_content: bool = False,
    ):
        """Inits ProxyRouter.

        Args:
        proxy_host -- The base URL of the target server to proxy requests to.
        stream_threshold -- Responses past this threshold will be streamed via chunked encoding.
        add_forwarded_headers -- If True, adds X-Forwarded-{For, Proto, Host} and Forwarded headers.
        preserve_host -- If True, preserves the Host header in the request.
        decode_content -- If True, decodes the response content based on the Content-Encoding header.
        """

        # Remove trailing slashes because the path will always start with /
        self.__proxy_host = proxy_host.rstrip("/")

        self.__stream_threshold = stream_threshold
        self.__add_x_forwarded = add_forwarded_headers
        self.__decode_content = decode_content
        self.__preserve_host = preserve_host

        self.__pool = PoolManager()
        self.http = HTTPResponseFactory()

    def __call__(self, conn_info: ConnectionInfo, request: HTTPRequest) -> HTTPResponse:
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
    ) -> HeaderContainer:
        # Process request headers
        headers = HeaderContainer(request.headers)
        for header in IGNORED_REQUEST_HEADERS:
            headers.pop(header, None)

        # Add X-Forwarded-* and Forwarded headers
        if self.__add_x_forwarded:
            # X-Forwarded-For
            x_forwarded_for = request.headers.get("X-Forwarded-For", None)
            headers["X-Forwarded-For"] = (
                f"{x_forwarded_for}, " if x_forwarded_for else ""
            ) + conn_info.remote_address.ip

            # X-Forwarded-Host
            if "Host" in request.headers:
                headers["X-Forwarded-Host"] = request.headers["Host"]

            # X-Forwarded-Proto
            headers["X-Forwarded-Proto"] = "https" if conn_info.secure else "http"

            # Forwarded
            forwarded = request.headers.get("Forwarded", None)
            headers["Forwarded"] = (f"{forwarded}, " if forwarded else "") + (
                f"by={conn_info.local_address.ip}"
                + f";for={conn_info.remote_address.ip}"
                + (
                    f";host={headers['X-Forwarded-Host']}"
                    if "X-Forwarded-Host" in headers
                    else ""
                )
                + f";proto={headers['X-Forwarded-Proto']}"
            )

        # Drop Host header if not preserving
        if not self.__preserve_host:
            headers.pop("host", None)

        return headers

    def __generate_response(self, response: BaseHTTPResponse) -> HTTPResponse:
        # Process response headers
        response_headers = HeaderContainer(response.headers)
        for header in IGNORED_RESPONSE_HEADERS:
            response_headers.pop(header, None)

        if self.__stream_required(response):
            return HTTPResponse(
                status_code=response.status,
                headers=HeaderContainer(response_headers),
                body=ResponseBody.from_stream(response),
            )
        else:
            return HTTPResponse(
                status_code=response.status,
                headers=HeaderContainer(response_headers),
                body=ResponseBody.from_bytes(response.data),
            )

    def __stream_required(self, response: BaseHTTPResponse) -> bool:
        # Stream responses if Transfer-Encoding is chunked
        if "Transfer-Encoding" in response.headers:
            if "chunked" in [
                x.strip().lower()
                for x in response.headers["Transfer-Encoding"].split(",")
            ]:
                return True

        # Stream if Content-Length is above threshold
        if "Content-Length" in response.headers:
            return int(response.headers["Content-Length"]) > self.__stream_threshold

        return False
