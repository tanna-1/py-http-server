from ..http.request_handler import RequestHandler
from ..networking.address import TCPAddress
from ..networking.connection import ConnectionThread
import socket
import threading
import ssl
import logging

LOG = logging.getLogger("listener")


class ListenerThread(threading.Thread):
    def __init__(
        self,
        socket: socket.socket,
        bind_address: TCPAddress,
        handler: RequestHandler,
    ):
        """
        Socket must already be in listening state.
        """
        super().__init__()
        self.__disposed = False
        self.__connections = []  # type: list[ConnectionThread]
        self.__socket = socket
        self.__bind_address = bind_address
        self.__handler = handler

    def run(self):
        if self.__disposed:
            raise RuntimeError("Cannot run a disposed ListenerThread")

        try:
            while True:
                # Clean disposed connections
                self.__clean_old_connections()

                # Wait for a connection
                conn, address = self.__socket.accept()
                parsed_address = TCPAddress(address[0], address[1])

                # Add new connection
                self.__add_connection(conn, parsed_address)
                LOG.debug(
                    f"({self.__bind_address}) Client connected from {parsed_address}"
                )
        except Exception as exc:
            # Suppress error messages on dispose() call
            if not self.__disposed:
                LOG.exception(
                    f"({self.__bind_address}) Error in ListenerThread", exc_info=exc
                )

        self.dispose()

    def __add_connection(self, conn: socket.socket, parsed_address: TCPAddress):
        self.__connections.append(
            ConnectionThread(conn, parsed_address, self.__handler)
        )
        self.__connections[-1].start()

    def __clean_old_connections(self):
        self.__connections = [c for c in self.__connections if not c.disposed]

    @property
    def disposed(self):
        return self.__disposed

    def dispose(self):
        if not self.__disposed:
            self.__disposed = True
            for connection in self.__connections:
                connection.dispose()
            self.__socket.close()
            LOG.info(f"({self.__bind_address}) Closed listener.")

    @staticmethod
    def create(bind_address: TCPAddress, handler_chain: list):
        """
        Will throw if the address can't be bound to.
        This method exists to avoid having a constructor that can throw.
        """
        sock_family = (
            socket.AF_INET if bind_address.ip_version == 4 else socket.AF_INET6
        )
        sock = socket.create_server(
            (bind_address.ip, bind_address.port),
            family=sock_family,
        )
        sock.listen()

        thread = ListenerThread(sock, bind_address, handler_chain)
        thread.start()
        return thread

    @staticmethod
    def create_ssl(
        bind_address: TCPAddress,
        handler,
        keyfile,
        certfile,
    ):
        """
        Will throw if the address can't be bound to.
        This method exists to avoid having a constructor that can throw.
        """
        sock_family = (
            socket.AF_INET if bind_address.ip_version == 4 else socket.AF_INET6
        )
        sock = socket.create_server(
            (bind_address.ip, bind_address.port),
            family=sock_family,
        )

        sock = ssl.wrap_socket(
            sock, keyfile=keyfile, certfile=certfile, server_side=True
        )
        sock.listen()

        thread = ListenerThread(sock, bind_address, handler)
        thread.start()
        return thread
