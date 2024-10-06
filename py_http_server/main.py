from .middlewares.default import DefaultMiddleware
from .networking.listener import ListenerThread
from .networking.address import TCPAddress
from .routers.file import FileRouter
from .middlewares.basic_auth import BasicAuthMiddleware
from .middlewares.compress import CompressMiddleware
from . import log
import time

LOG = log.getLogger("main")


def app_main():
    log.init()
    try:
        HTTP_BIND_ADDRESSES = [
            TCPAddress("127.0.0.1", 80),
            TCPAddress("::1", 80),
        ]  # type: list[TCPAddress]
        HTTPS_BIND_ADDRESSES = []  # type: list[TCPAddress]
        HTTPS_KEY_FILE = ""
        HTTPS_CERT_FILE = ""
        HANDLER = CompressMiddleware(
            DefaultMiddleware(
                BasicAuthMiddleware(FileRouter("."), credentials={"test": "test"})
            )
        )

        listeners = []  # type: list[ListenerThread]

        # Create HTTP listeners
        for address in HTTP_BIND_ADDRESSES:
            try:
                listeners.append(ListenerThread.create(address, HANDLER))
                LOG.info(f"New HTTP listener on {address}")
            except Exception as exc:
                LOG.exception(
                    f"Failed to create a HTTP listener on {address}", exc_info=exc
                )

        # Create HTTPS listeners
        for address in HTTPS_BIND_ADDRESSES:
            try:
                listeners.append(
                    ListenerThread.create_ssl(
                        address, HANDLER, HTTPS_KEY_FILE, HTTPS_CERT_FILE
                    )
                )
                LOG.info(f"New HTTPS listener on {address}")
            except Exception as exc:
                LOG.exception(
                    f"Failed to create a HTTPS listener on {address}", exc_info=exc
                )

        try:
            while len(listeners) > 0:
                # Clean disposed listeners
                listeners = [l for l in listeners if not l.disposed]
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        LOG.info("Exiting...")
        for listener in listeners:
            listener.dispose()
    except Exception as exc:
        LOG.fatal("Unrecoverable error", exc_info=exc)
    log.shutdown()
