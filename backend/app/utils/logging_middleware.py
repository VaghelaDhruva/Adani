import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        method = request.method
        url = str(request.url)
        client_ip = request.client.host if request.client else "unknown"

        response: Response = await call_next(request)
        process_time = time.time() - start_time
        status_code = response.status_code

        logger.info(
            "API request",
            extra={
                "method": method,
                "url": url,
                "client_ip": client_ip,
                "status_code": status_code,
                "process_time_seconds": process_time,
            },
        )
        return response
