import socket
import threading

from http_request import receive_http_request
from router import DebugRouter, SourceAddress

LISTEN_IP = "127.0.0.1"
LISTEN_PORT = 80
ROUTER = DebugRouter()


class ClientThread(threading.Thread):
    def __init__(self, conn: socket.socket, address: SourceAddress):
        super().__init__()
        self.__conn = conn
        self.__address = address
        self.__disposed = False

    def run(self):
        try:
            while True:
                req = receive_http_request(self.__conn)
                self.__log(req)
                resp = ROUTER.handle(self.__address, req)
                self.__conn.send(resp.as_bytes())

                # Close connection if not keep-alive
                if req.headers.get("connection", "close") != "keep-alive":
                    break
        except Exception as exc:
            self.__log(f"Exception: {exc}")
        self.dispose()

    def __log(self, message: str):
        print(f"[{self.__address}] {message}")

    @property
    def disposed(self):
        return self.__disposed

    def dispose(self):
        self.__conn.close()
        self.__disposed = True
        self.__log("Closed connection.")


def main():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((LISTEN_IP, LISTEN_PORT))
        s.listen()
        print(f"[*] Started server on http://{LISTEN_IP}:{LISTEN_PORT}")
    except socket.error:
        print("[!] Failed to create socket")
        return

    clients = []
    while True:
        clients = [client for client in clients if not client.disposed]
        conn, address = s.accept()
        parsed_address = SourceAddress(address[0], address[1])
        clients.append(ClientThread(conn, parsed_address))
        clients[-1].start()
        print(f"[+] Client connected from {parsed_address}")


if __name__ == "__main__":
    main()
