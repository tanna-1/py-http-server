from http11.request import HTTPRequest
from http11.response import HTTPResponse, HTTPResponseFactory
from networking.address import TCPAddress
from routers.base import Router
from pathlib import Path
from datetime import datetime
import html
import mimetypes
import urllib.parse
import os
import logging
import hashlib


LOG = logging.getLogger("routers.file")
CHUNK_THRESHOLD = 1048576  # 1MiB


class FileRouter(Router):
    def __init__(
        self,
        document_root: str | os.PathLike,
        generate_index: bool = True,
        generate_etag: bool = True,
    ) -> None:
        super().__init__(
            HTTPResponseFactory(
                {
                    "X-Powered-By": "Tan's HTTP Server",
                    "Cache-Control": "no-cache, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                }
            )
        )

        self.__document_root = Path(document_root).resolve()
        self.__generate_index = generate_index
        self.__generate_etag = generate_etag

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

    def _handle(self, requester: TCPAddress, request: HTTPRequest):
        if request.method != "GET":
            return 400

        raw_path = urllib.parse.unquote(request.path.lstrip("/"))
        full_path = self.__document_root.joinpath(raw_path).resolve()

        # Prevent path traversal!
        if not self.__is_path_allowed(full_path):
            LOG.warning(f"Attempted path traversal! Returning 400.")
            return 400

        try:
            if full_path.is_file():
                return self.serve_file(request, full_path)
            elif full_path.is_dir():
                index_html = full_path.joinpath("index.html")
                if index_html.is_file():
                    return self.serve_file(request, index_html)
                elif self.__generate_index:
                    # Generate index if allowe and there is no index.html
                    return self.serve_folder(full_path)
        except Exception as exc:
            LOG.exception("Error while accesing path", exc_info=exc)
            return 500

        return 404

    def serve_file(self, request: HTTPRequest, path: Path):
        with path.open("rb") as f:
            LOG.debug(f'Reading file "{path}"')
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(0, os.SEEK_SET)

            if size > CHUNK_THRESHOLD:
                # Not implemented yet.
                return 500

            headers = {}
            if self.__generate_etag:
                etag = f'"{hashlib.file_digest(f, "sha256").hexdigest()}"'
                headers["ETag"] = etag
                f.seek(0, os.SEEK_SET)

                # Return 304 with ETag
                if etag == request.headers.get("if-none-match", None):
                    return self.resp_factory.status(304, headers)

            headers["Content-Type"] = self.__get_content_type(path)
            return HTTPResponse(200, headers, f.read(size))

    def serve_folder(self, path: Path):
        # Turns any path into an absolute web path (relative to document root)
        def make_link(p: Path) -> str:
            rel_p = p.relative_to(self.__document_root)
            return urllib.parse.quote("/" + rel_p.as_posix())

        # Escapes text for embedding within HTML
        def make_text(val):
            return html.escape(str(val))

        # Display path relative to document root without quoting
        content = f"<!DOCTYPE html><html><body><h3>{make_text(path.relative_to(self.__document_root))}</h3><ul>"

        # Display the parent path if possible
        if path.parent != path and self.__is_path_allowed(path.parent):
            content += f'<li><a href="{make_link(path.parent)}">..</a></li>'

        # Display entries for sub paths
        for sub_path in path.iterdir():
            content += f'<li><a href="{make_link(sub_path)}">{make_text(sub_path.name)}</a></li>'

        content += (
            f"</ul><p>Generated on {datetime.now().isoformat()}</p></body></html>"
        )
        return self.resp_factory.html(content)
