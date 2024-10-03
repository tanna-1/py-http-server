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
        disable_symlinks: bool = True,
    ) -> None:
        """Inits FileRouter.

        Args:
        document_root -- Document root.
        generate_index -- If True, generated index pages will be served for directories.
        generate_etag -- If True, ETag will be calculated and sent with every response.
        disable_symlinks -- If True, symlinks won't be followed.

        WARNING: Enabling symlinks may lead to unexpected results with authentication middlewares.
        E.g. "/protected_folder" vs "/folder/../protected_folder"
        """

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
        self.__disable_symlinks = disable_symlinks

    def __is_path_allowed(self, path: Path):
        resolved_path = path.resolve()
        if self.__disable_symlinks:
            if path != resolved_path:
                return False

        # Resolved path must be within document root
        return resolved_path.is_relative_to(self.__document_root)

    def __get_content_type(self, path: Path) -> str:
        ret = "application/octet-stream"
        mime_type, encoding = mimetypes.guess_type(path, False)
        if mime_type:
            ret = f"{mime_type}"
            if encoding:
                ret += f"; charset={encoding}"
        return ret

    def __serve_file(self, request: HTTPRequest, path: Path):
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
                    return self._httpf.status(304, headers)

            headers["Content-Type"] = self.__get_content_type(path)
            return HTTPResponse(200, headers, f.read(size))

    def __serve_folder(self, requester: TCPAddress, path: Path):
        # Turns any path into an absolute web path (relative to document root)
        def make_link(p: Path) -> str:
            rel_p = p.relative_to(self.__document_root)
            return urllib.parse.quote("/" + rel_p.as_posix())

        # Escapes text for embedding within HTML
        def make_text(val):
            return html.escape(str(val))

        # Display path relative to document root
        title = make_text(path.relative_to(self.__document_root).as_posix())
        content = f"<!DOCTYPE html><html><head><title>{title}</title></head><body><h3>{title}</h3><ul>"

        # Display the parent path if possible
        if path.parent != path and self.__is_path_allowed(path.parent):
            content += f'<li><a href="{make_link(path.parent)}">..</a></li>'

        # Display entries for sub paths
        for sub_path in path.iterdir():
            content += f'<li><a href="{make_link(sub_path)}">{make_text(sub_path.name)}</a></li>'

        content += f"</ul><p>Generated on {datetime.now().isoformat()} for {requester}</p></body></html>"
        return self._httpf.html(content)

    def _handle(self, requester: TCPAddress, request: HTTPRequest):
        if request.method != "GET":
            return 400

        # Unquote HTTP path, append it to document root
        # The path is unsafe at this point
        path = self.__document_root.joinpath(
            urllib.parse.unquote(request.path.lstrip("/"))
        )

        # Prevent path traversal and optionally forbid symlinks
        if not self.__is_path_allowed(path):
            LOG.warning(f"Path not allowed: {path}")
            return 403

        try:
            if path.is_file():
                return self.__serve_file(request, path)
            elif path.is_dir():
                index_html = path.joinpath("index.html")
                if index_html.is_file():
                    return self.__serve_file(request, index_html)
                elif self.__generate_index:
                    # Generate index if allowe and there is no index.html
                    return self.__serve_folder(requester, path)
        except Exception as exc:
            LOG.exception("Error while accesing path", exc_info=exc)
            return 500

        return 404
