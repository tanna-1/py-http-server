from networking.address import TCPAddress
from http11.request import HTTPRequest
from router import Router
import socket
import threading


class ConnectionThread(threading.Thread):
    def __init__(self, conn: socket.socket, address: TCPAddress, router: Router):
        super().__init__()
        self.__conn = conn
        self.__address = address
        self.__router = router
        self.__disposed = False

    def run(self):
        if self.__disposed:
            raise RuntimeError("Cannot run a disposed ConnectionThread")

        try:
            while True:
                # Read request from socket
                req = HTTPRequest.receive_from(self.__conn)
                self.__log(req)

                # Pass the request to router
                resp = self.__router.handle(self.__address, req)

                # Send the response from router
                self.__conn.send(resp.build(http_version=req.version))

                # Close connection if not keep-alive
                if req.headers.get("connection", "close") != "keep-alive":
                    break
        except Exception as exc:
            # Suppress error messages on dispose() call
            if not self.__disposed:
                self.__log(f"{exc}")
        
        self.dispose()

    def __log(self, message: str):
        print(f"[connection] {self.__address} {message}")

    @property
    def disposed(self):
        return self.__disposed

    def dispose(self):
        if not self.__disposed:
            self.__disposed = True
            self.__conn.close()
            self.__log("Closed connection.")
