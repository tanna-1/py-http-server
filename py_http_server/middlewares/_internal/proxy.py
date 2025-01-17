from ...common import RequestHandlerABC, RequestHandler
from ...networking import ConnectionInfo
from ...http.request import HTTPRequest

IGNORED_REQUEST_HEADERS = {"Connection", "TE"}
IGNORED_RESPONSE_HEADERS = {"Connection", "Transfer-Encoding"}


class _ProxyPreprocessMiddleware(RequestHandlerABC):
    def __init__(
        self, next: RequestHandler, set_proxy_headers: bool, preserve_host: bool
    ):
        self.next = next
        self.__set_proxy_headers = set_proxy_headers
        self.__preserve_host = preserve_host

    def __call__(self, conn_info: ConnectionInfo, request: HTTPRequest):
        # Drop ignored headers
        for header in IGNORED_REQUEST_HEADERS:
            request.headers.pop(header, None)

        # Add X-Forwarded-* and Forwarded headers
        if self.__set_proxy_headers:
            # X-Forwarded-For
            x_forwarded_for = request.headers.get("X-Forwarded-For", None)
            request.headers["X-Forwarded-For"] = (
                f"{x_forwarded_for}, " if x_forwarded_for else ""
            ) + conn_info.remote_address.ip

            # X-Forwarded-Host
            if "Host" in request.headers:
                request.headers["X-Forwarded-Host"] = request.headers["Host"]

            # X-Forwarded-Proto
            request.headers["X-Forwarded-Proto"] = (
                "https" if conn_info.secure else "http"
            )

            # Forwarded
            forwarded = request.headers.get("Forwarded", None)
            request.headers["Forwarded"] = (f"{forwarded}, " if forwarded else "") + (
                f"by={conn_info.local_address.ip}"
                + f";for={conn_info.remote_address.ip}"
                + (
                    f";host={request.headers['X-Forwarded-Host']}"
                    if "X-Forwarded-Host" in request.headers
                    else ""
                )
                + f";proto={request.headers['X-Forwarded-Proto']}"
            )

        # Drop Host header if not preserving
        if not self.__preserve_host:
            request.headers.pop("Host", None)

        return self.next(conn_info, request)


class _ProxyPostprocessMiddleware(RequestHandlerABC):
    def __init__(self, next: RequestHandler):
        self.next = next

    def __call__(self, conn_info: ConnectionInfo, request: HTTPRequest):
        resp = self.next(conn_info, request)

        # Drop ignored headers
        for header in IGNORED_RESPONSE_HEADERS:
            resp.headers.pop(header, None)

        return resp
