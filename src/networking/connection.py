from http11.request_handler import RequestHandler
from networking.address import TCPAddress
from http11.request import HTTPRequest
import socket
import threading
import logging

LOG = logging.getLogger("connection")


class ConnectionThread(threading.Thread):
    def __init__(
        self,
        conn: socket.socket,
        requester: TCPAddress,
        handler: RequestHandler,
    ):
        super().__init__()
        self.__conn = conn
        self.__requester = requester
        self.__handler = handler
        self.__disposed = False

    @staticmethod
    def __get_connection_policy(req: HTTPRequest) -> True:
        if req.version == "HTTP1.0":
            # "close" by default unless "keep-alive" specified
            if req.headers.get("connection", None) != "keep-alive":
                return "close"
        elif req.version == "HTTP1.1":
            # "close" only if "close" specified
            if req.headers.get("connection", None) == "close":
                return "close"
        return "keep-alive"

    def run(self):
        if self.__disposed:
            raise RuntimeError("Cannot run a disposed ConnectionThread")

        try:
            while True:
                # Read request from socket
                req = HTTPRequest.receive_from(self.__conn)
                LOG.info(f"({self.__requester}) {req}")

                # Execute the handler chain
                resp = self.__handler(self.__requester, req)
                conn_policy = self.__get_connection_policy(req)
                resp.headers["Connection"] = conn_policy

                # Send the response
                resp.send_to(self.__conn, req.version)

                # Close the connection if necessary
                if conn_policy == "close":
                    break
        except Exception as exc:
            # Suppress error messages on dispose() call
            if not self.__disposed:
                LOG.exception(
                    f"({self.__requester}) Error in ConnectionThread", exc_info=exc
                )

        self.dispose()

    @property
    def disposed(self):
        return self.__disposed

    def dispose(self):
        if not self.__disposed:
            self.__disposed = True
            self.__conn.close()
            LOG.debug(f"({self.__requester}) Closed connection.")
