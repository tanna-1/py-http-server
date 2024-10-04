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
        handler,
    ):
        super().__init__()
        self.__conn = conn
        self.__requester = requester
        self.__handler = handler
        self.__disposed = False

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

                if not resp:
                    raise RuntimeError("Handler chain did not produce a response")

                # Send the response
                resp.send_to(self.__conn, req.version)

                # Close connection if not keep-alive
                if req.headers.get("connection", "close") != "keep-alive":
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
