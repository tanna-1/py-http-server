from ..http.constants import NO_CACHE_HEADERS
from ..http.request import HTTPRequest
from ..common import RequestHandler
from ..http.response import HTTPResponseFactory
from ..networking.address import TCPAddress
from ..middlewares.base import Middleware
from .. import log
import base64

LOG = log.getLogger("middlewares.basic_auth")


class BasicAuthMiddleware(Middleware):
    def __init__(self, next: RequestHandler, credentials: dict[str, str]):
        self.next = next
        self.__cred = credentials
        self.http = HTTPResponseFactory(NO_CACHE_HEADERS)

    def __verify_authorization(self, header_value: str):
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

        return self.http.status(
            401,
            {"WWW-Authenticate": 'Basic realm="auth", charset="UTF-8"'},
        )
