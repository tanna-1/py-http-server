import ipaddress
from .. import log
from typing import Literal


class TCPAddress:
    def __init__(self, ip: str, port: int):
        if not isinstance(port, int) or port < 0 or port > 65535:
            raise ValueError("Invalid port")

        if not isinstance(ip, str) or not ip:
            raise ValueError("Invalid IP")

        self.__ipversion = ipaddress.ip_address(ip).version  # type: Literal[4, 6]
        self.__ip = ip
        self.__port = port

    @property
    def ip(self):
        return self.__ip

    @property
    def ip_version(self):
        return self.__ipversion

    @property
    def port(self):
        return self.__port

    def __str__(self):
        if self.__ipversion == 6:
            return f"[{self.__ip}]:{self.__port}"
        return f"{self.__ip}:{self.__port}"
