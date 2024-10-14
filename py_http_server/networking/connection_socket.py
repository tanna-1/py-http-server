import socket


class GracefulDisconnectException(Exception):
    pass


class ConnectionSocket:
    """
    A socket.socket wrapper class to make handling remote disconnects and closes easier.
    """

    def __init__(self, socket: socket.socket):
        self.__socket = socket

    def recv(self, bufsize: int, flags: int = 0) -> bytes:
        ret = self.__socket.recv(bufsize, flags)
        if len(ret) == 0:
            raise GracefulDisconnectException()
        return ret

    def send(self, data, flags: int = 0) -> int:
        return self.__socket.send(data, flags)

    def sendfile(self, file, offset=0, count=None):
        return self.__socket.sendfile(file, offset, count)

    def close(self):
        # Try to shutdown the socket, this is required on Linux
        # otherwise some socket functions won't return!
        try:
            self.__socket.shutdown(socket.SHUT_RD)
        except:
            pass
        self.__socket.close()
