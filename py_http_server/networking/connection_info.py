from ..networking.address import TCPAddress


class ConnectionInfo:
    def __init__(
        self, remote_address: TCPAddress, local_address: TCPAddress, secure: bool
    ):
        self.__remote_address = remote_address
        self.__local_address = local_address
        self.__secure = secure

    @property
    def remote_address(self) -> TCPAddress:
        return self.__remote_address

    @property
    def local_address(self) -> TCPAddress:
        return self.__local_address

    @property
    def secure(self) -> bool:
        return self.__secure
