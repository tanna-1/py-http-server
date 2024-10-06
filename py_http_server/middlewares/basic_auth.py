from ..http.request import HTTPRequest
from ..http.request_handler import RequestHandler
from ..http.response import HTTPResponseFactory
from ..networking.address import TCPAddress
from ..middlewares.base import Middleware
from .. import log
import base64

LOG = log.getLogger("middlewares.basic_auth")


class BasicAuthMiddleware(Middleware):
    def __init__(self, next: RequestHandler, credentials: dict[str, str]) -> None:
        super().__init__(next)
        self.__cred = credentials
        self.__http = HTTPResponseFactory(
            {
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            }
        )

    def __verify_authorization(self, header_value: str) -> bool:
        auth_type, _, data = header_value.partition(" ")
        if not data or auth_type != "Basic":
            return False
        username, _, password = (
            base64.b64decode(data).decode("utf-8", "replace").partition(":")
        )

        if username in self.__cred and self.__cred[username] == password:
            LOG.debug(f"Basic authentication correct credentials.")
            return True

        LOG.warning(f"Basic authentication incorrect credentials.")
        return False

    def __call__(self, requester: TCPAddress, request: HTTPRequest):
        if "authorization" in request.headers and self.__verify_authorization(
            request.headers["authorization"]
        ):
            return self.next(requester, request)

        return self.__http.status(
            401,
            {"WWW-Authenticate": 'Basic realm="auth", charset="UTF-8"'},
        )