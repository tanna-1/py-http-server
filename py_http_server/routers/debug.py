from ..networking import ConnectionInfo
from ..http.request import HTTPRequest
from ..routers.code import CodeRouter, route


class DebugRouter(CodeRouter):
    @route("/json")
    def json_page(self, conn_info: ConnectionInfo, request: HTTPRequest):
        return self.http.json(
            {
                "remote_address": conn_info.remote_address,
                "request": {
                    "headers": request.headers,
                    "path": request.path,
                    "query": request.query,
                    "method": request.method,
                    "version": request.version,
                    "body": request.body.decode("ascii", "replace"),
                },
            }
        )

    @route("/")
    def root_page(self, conn_info: ConnectionInfo, request: HTTPRequest):
        content = f'<!DOCTYPE html><html><body><a href="/json">Try the /json page</a>'
        content += f"<h3>Remote Address</h3><p>{conn_info.remote_address}</p>"
        content += f"<h3>Request Path</h3><p>{request.path}</p>"
        content += f"<h3>Request Query</h3><p>{request.query}</p>"
        content += f"<h3>Request Method</h3><p>{request.method}</p>"
        content += "<h3>Request Headers</h3><ul>"
        for key, value in request.headers.items():
            content += f"<li>{key}: {value}</li>"
        content += "</ul></body></html>"
        return self.http.html(content)

    @route("/error")
    def error_page(self, conn_info: ConnectionInfo, request: HTTPRequest):
        raise RuntimeError("DebugRouter test exception")
