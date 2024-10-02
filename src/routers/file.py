from http11.request import HTTPRequest
from http11.response import HTTPResponse
from networking.address import TCPAddress
from routers.base import Router
from pathlib import Path
from datetime import datetime
import mimetypes
import urllib.parse
import os
import logging


LOG = logging.getLogger("routers.file")
CHUNK_THRESHOLD = 1048576  # 1MiB


class FileRouter(Router):
    def __init__(
        self, document_root: str | os.PathLike, generate_index: bool = True
    ) -> None:
        super().__init__()

        self.__html_headers = {
            "Content-Type": "text/html; charset=utf-8",
            "X-Powered-By": "Tan's HTTP Server",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }  # type: dict[str, str]

        self.__file_headers = {
            "Content-Type": "application/octet-stream",
            "X-Powered-By": "Tan's HTTP Server",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }  # type: dict[str, str]

        self.__document_root = Path(document_root).resolve()
        self.__generate_index = generate_index

    def __is_path_allowed(self, path: Path):
        return path.is_relative_to(self.__document_root)

    def __get_content_type(self, path: Path) -> str:
        ret = "application/octet-stream"
        mime_type, encoding = mimetypes.guess_type(path, False)
        if mime_type:
            ret = f"{mime_type}"
            if encoding:
                ret += f"; charset={encoding}"
        return ret

    def handle(self, requester: TCPAddress, request: HTTPRequest) -> HTTPResponse:
        if request.method != "GET":
            return self.not_found_page(requester, request)

        full_path = self.__document_root.joinpath(request.path.lstrip("/")).resolve()

        # Prevent path traversal!
        if not self.__is_path_allowed(full_path):
            LOG.warning(f"Attempted path traversal! Returning 404.")
            return self.not_found_page(requester, request)

        if full_path.is_file():
            return self.serve_file(requester, request, full_path)
        elif full_path.is_dir():
            index_html = full_path.joinpath("index.html")
            if index_html.is_file():
                return self.serve_file(requester, request, index_html)
            elif self.__generate_index:
                # Generate index if allowe and there is no index.html
                return self.serve_folder(requester, request, full_path)

        return self.not_found_page(requester, request)

    def serve_file(
        self, requester: TCPAddress, request: HTTPRequest, path: Path
    ) -> HTTPResponse:
        try:
            with path.open("rb") as f:
                LOG.info(f'Reading file "{path}"')
                f.seek(0, os.SEEK_END)
                size = f.tell()
                f.seek(0, os.SEEK_SET)

                if size > CHUNK_THRESHOLD:
                    # Not implemented yet.
                    return self.internal_error_page(requester, request)

                headers = dict(self.__file_headers)
                headers["Content-Type"] = self.__get_content_type(path)
                return HTTPResponse(200, headers, f.read(size))
        except Exception as exc:
            LOG.exception("Error while reading file.", exc_info=exc)
            return self.internal_error_page(requester, request)

    def serve_folder(
        self, requester: TCPAddress, request: HTTPRequest, path: Path
    ) -> HTTPResponse:
        # Turns any path into an absolute web path (relative to document root)
        def make_link(p: Path) -> str:
            rel_p = p.relative_to(self.__document_root)
            return urllib.parse.quote("/" + rel_p.as_posix())

        content = f"<!DOCTYPE html><html><body><h3>{make_link(path)}</h3><ul>"

        # Display the parent path if possible
        if self.__is_path_allowed(path.parent):
            content += f'<li><a href="{make_link(path.parent)}">..</a></li>'

        # Display entries for sub paths
        for sub_path in path.iterdir():
            content += f'<li><a href="{make_link(sub_path)}">{sub_path.name}</a></li>'

        content += (
            f"</ul><p>Generated on {datetime.now().isoformat()}</p></body></html>"
        )
        return HTTPResponse(200, self.__html_headers, content.encode("utf-8"))

    def internal_error_page(
        self, requester: TCPAddress, request: HTTPRequest
    ) -> HTTPResponse:
        return HTTPResponse(500, self.__html_headers, b"500 Internal Server Error")

    def not_found_page(
        self, requester: TCPAddress, request: HTTPRequest
    ) -> HTTPResponse:
        return HTTPResponse(404, self.__html_headers, b"404 Not Found")
