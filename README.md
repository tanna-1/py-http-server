# py-http-server

## About
This project implements an HTTP(S) server supporting HTTP versions 1.0 and 1.1.

## Configuration
To configure the server, `py_http_server.app_main()` can be called from a Python script with custom arguments.

The argument `handler_chain` can be constructed using user-defined classes or built-in components like below.

```python
from py_http_server.middlewares import CompressMiddleware, DefaultMiddleware
from py_http_server.routers import FileRouter
from py_http_server.networking import TCPAddress
from py_http_server import app_main

app_main(
    handler_chain=DefaultMiddleware(CompressMiddleware(FileRouter("."))),
    http_listeners=[
        TCPAddress("127.0.0.1", 80),
        TCPAddress("::1", 80),
    ],
)
```

### Middlewares
1. **BasicAuthMiddleware**  
   Enforces basic HTTP authentication for all requests.

2. **CompressMiddleware**  
   Compresses responses based on client's `Accept-Encoding` value, supports `gzip`, `brotli`, `zstd` and `deflate`.

3. **DefaultMiddleware**  
   Adds default headers `Server` and `Date` to all responses.

### Routers
> [!NOTE]
> `CodeRouter` is a base class and cannot be used on its own.

1. **CodeRouter**  
   Auto-discovers route handlers using a `@route(path)` decorator for mapping paths to handler functions.  

2. **DebugRouter**  
   Provides predefined routes for debugging:
   - `/`: Displays request details in HTML.
   - `/json`: Displays request details in JSON.
   - `/error`: Raises an error in the route handler.

3. **FileRouter**  
   Serves static files from a specified directory. Supports `ETag`, `Last-Modified` headers, and generated directory index pages.
