from http11.request import HTTPRequest
from networking.address import TCPAddress
from routers.code import CodeRouter, route


class DebugRouter(CodeRouter):
    @route("/json")
    def json_page(self, requester: TCPAddress, request: HTTPRequest):
        return self.json(
            {
                "requester": str(requester),
                "request": {
                    "headers": request.headers,
                    "path": request.path,
                    "query": request.query,
                    "method": request.method,
                    "version": request.version,
                    "body": request.body.decode("ascii", "ignore"),
                },
            }
        )

    @route("/")
    def root_page(self, requester: TCPAddress, request: HTTPRequest):
        content = f'<!DOCTYPE html><html><body><a href="/json">Try the /json page</a>'
        content += f"<h3>Source Address</h3><p>{requester}</p>"
        content += f"<h3>Request Path</h3><p>{request.path}</p>"
        content += f"<h3>Request Query</h3><p>{request.query}</p>"
        content += f"<h3>Request Method</h3><p>{request.method}</p>"
        content += "<h3>Request Headers</h3><ul>"
        for key, value in request.headers.items():
            content += f"<li>{key}: {value}</li>"
        content += "</ul></body></html>"
        return self.html(content)

    @route("/error")
    def error_page(self, requester: TCPAddress, request: HTTPRequest):
        raise RuntimeError("DebugRouter test exception")
