from pathlib import Path
from abc import ABC, abstractmethod
from io import IOBase
from ..common.constants import HeaderContainer
from ..networking.connection_socket import ConnectionSocket


class ResponseBody(ABC):
    def __bool__(self) -> bool:
        return True

    @abstractmethod
    def __len__(self) -> int: ...

    @property
    @abstractmethod
    def headers(self) -> HeaderContainer: ...

    @abstractmethod
    def send_to(self, conn: ConnectionSocket) -> None: ...

    @staticmethod
    def from_file(file_path: Path):
        return FileBody(file_path)

    @staticmethod
    def from_bytes(value: bytes):
        return BytesBody(value)

    @staticmethod
    def from_stream(stream: IOBase):
        return StreamingBody(stream)


class StreamingBody(ResponseBody):
    LAST_CHUNK = b"0\r\n"
    TRAILER = b"\r\n"

    def __init__(self, stream: IOBase, stream_chunk_size: int = 1048576):
        self.stream = stream
        self.__stream_chunk_size = stream_chunk_size

    def __len__(self):
        return 0

    @property
    def stream(self) -> IOBase:
        return self.__stream

    @stream.setter
    def stream(self, value: IOBase):
        self.__stream = value

    @property
    def headers(self) -> HeaderContainer:
        return HeaderContainer({"Transfer-Encoding": "chunked"})

    def __get_chunk_size(self, val: bytes) -> bytes:
        return hex(len(val))[2:].upper().encode() + b"\r\n"

    def __make_chunk(self, val: bytes) -> bytes:
        return self.__get_chunk_size(val) + val + b"\r\n"

    def send_to(self, conn: ConnectionSocket):
        while True:
            chunk = self.__stream.read(self.__stream_chunk_size)
            if not chunk:
                break
            conn.send(self.__make_chunk(chunk))
        conn.send(self.LAST_CHUNK + self.TRAILER)


class FileBody(ResponseBody):
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def __len__(self):
        return self.__len

    @property
    def file_path(self) -> Path:
        return self.__file_path

    @file_path.setter
    def file_path(self, value: Path):
        self.__file_path = value
        self.__len = value.stat().st_size

    @property
    def headers(self) -> HeaderContainer:
        return HeaderContainer({"Content-Length": str(len(self))})

    def send_to(self, conn: ConnectionSocket):
        with self.__file_path.open("rb") as f:
            conn.sendfile(f)


class BytesBody(ResponseBody):
    def __init__(self, content: bytes):
        self.content = content

    def __len__(self):
        return len(self.__content)

    @property
    def content(self) -> bytes:
        return self.__content

    @content.setter
    def content(self, value: bytes):
        self.__content = value

    @property
    def headers(self) -> HeaderContainer:
        return HeaderContainer({"Content-Length": str(len(self))})

    def send_to(self, conn: ConnectionSocket):
        conn.send(self.content)


# EmptyBody has no Content-Length header, to be used for HEAD responses
class EmptyBody(ResponseBody):
    def __len__(self):
        return 0

    @property
    def headers(self) -> HeaderContainer:
        return HeaderContainer()

    def send_to(self, conn: ConnectionSocket):
        pass
