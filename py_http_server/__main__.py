from .middlewares.default import DefaultMiddleware
from .networking.address import TCPAddress
from .routers.file import FileRouter
from .middlewares.compress import CompressMiddleware
from .main import app_main

if __name__ == "__main__":
    app_main(
        handler_chain=CompressMiddleware(DefaultMiddleware(FileRouter("."))),
        http_listeners=[
            TCPAddress("127.0.0.1", 80),
            TCPAddress("::1", 80),
        ],
    )
