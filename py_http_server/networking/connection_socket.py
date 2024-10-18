import socket
from platform import platform

_PLATFORM = platform()
_SOCKET_NOPUSH_OPTION = None
if _PLATFORM.startswith("FreeBSD"):
    _SOCKET_NOPUSH_OPTION = 0x04
elif _PLATFORM.startswith("OpenBSD"):
    _SOCKET_NOPUSH_OPTION = 0x10
elif _PLATFORM.startswith("Linux"):
    _SOCKET_NOPUSH_OPTION = socket.TCP_CORK
# Windows doesn't have an equivalent


class GracefulDisconnectException(Exception):
    pass


class ConnectionSocket:
    """
    A socket.socket wrapper class to make handling remote disconnects and closes easier.
    """

    def __init__(
        self,
        sock: socket.socket,
        enable_sendfile: bool = True,
        enable_nopush: bool = True,
        enable_nodelay: bool = False,
    ):
        """
        enable_sendfile: When set to True, an attempt will be made to use sendfile, enabled by default.
        enable_nopush: Behaves like Nginx's "tcp_nopush", enabled by default.
        enable_nodelay: Behaves like Nginx's "tcp_nodelay", disabled by default.
        """
        if _SOCKET_NOPUSH_OPTION != None:
            sock.setsockopt(socket.IPPROTO_TCP, _SOCKET_NOPUSH_OPTION, enable_nopush)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, enable_nodelay)

        self.__enable_nodelay = enable_nodelay
        self.__socket = sock
        self.__enable_sendfile = enable_sendfile

    def recv(self, bufsize: int, flags: int = 0) -> bytes:
        ret = self.__socket.recv(bufsize, flags)
        if len(ret) == 0:
            raise GracefulDisconnectException()
        return ret

    def send(self, data, flags: int = 0) -> int:
        return self.__socket.send(data, flags)

    def sendfile(self, file, offset=0, count=None):
        if self.__enable_sendfile:
            return self.__socket.sendfile(file, offset, count)
        else:
            return self.__socket._sendfile_use_send(file, offset, count)
        
    def flush(self):
        # Force flush of the socket. Only tested on Linux.
        if not self.__enable_nodelay:
            self.__socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
            self.__socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, False)

    def close(self):
        # Try to shutdown the socket, this is required on Linux
        # otherwise some socket functions won't return!
        try:
            self.__socket.shutdown(socket.SHUT_RD)
        except:
            pass
        self.__socket.close()
