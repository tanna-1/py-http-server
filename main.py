from networking.listener import ListenerThread
from networking.address import TCPAddress
from router import DebugRouter
import time

LISTEN_ADDR = [
    TCPAddress("127.0.0.1", 80),
    TCPAddress("::1", 80),
]  # type: list[TCPAddress]
ROUTER = DebugRouter()


def main():
    listeners = []  # type: list[ListenerThread]
    for address in LISTEN_ADDR:
        try:
            listeners.append(ListenerThread.create(address, ROUTER))
            print(f"[+] New listener on {address}")
        except Exception as exc:
            print(f"[*] Failed to create a listener on {address}. {exc}")

    try:
        while len(listeners) > 0:
            # Clean disposed listeners
            listeners = [l for l in listeners if not l.disposed]
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    print("[*] Exiting...")


if __name__ == "__main__":
    main()
