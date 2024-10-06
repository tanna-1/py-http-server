# py-http-server

## About
This project implements an HTTP(S) server supporting HTTP versions 1.0 and 1.1.

## Configuration
All configuration is in `__main__.py`. Set the `HANDLER` variable to construct handler chains using components below.

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
