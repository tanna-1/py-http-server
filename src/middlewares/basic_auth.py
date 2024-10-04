from http11.request import HTTPRequest
from http11.request_handler import RequestHandler
from http11.response import HTTPResponseFactory
from networking.address import TCPAddress
from middlewares.base import Middleware
import logging
import base64

LOG = logging.getLogger("middlewares.basic_auth")


class BasicAuthMiddleware(Middleware):
    def __init__(self, credentials: dict[str, str], next: RequestHandler) -> None:
        self.__cred = credentials
        super().__init__(
            next,
            HTTPResponseFactory(
                {
                    "X-Powered-By": "Tan's HTTP Server",
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                }
            ),
        )

    def __verify_authorization(self, header_value: str) -> bool:
        auth_type, _, data = header_value.partition(" ")
        if not data or auth_type != "Basic":
            return False
        username, _, password = (
            base64.b64decode(data).decode("utf-8", "replace").partition(":")
        )

        if username in self.__cred and self.__cred[username] == password:
            LOG.debug(
                f'Basic authentication values "{username}:{password}" are correct.'
            )
            return True

        LOG.warning(
            f'Basic authentication values "{username}:{password}" are incorrect.'
        )
        return False

    def _handle(self, requester: TCPAddress, request: HTTPRequest):
        if "authorization" in request.headers and self.__verify_authorization(
            request.headers["authorization"]
        ):
            return self.next(requester, request)

        return self._httpf.status(
            401,
            {"WWW-Authenticate": 'Basic realm="auth", charset="UTF-8"'},
        )
