import time

from fastapi import Request

from app.core.logging import setup_logging

logger = setup_logging()


async def logging_middleware(request: Request, call_next):
    start_time = time.perf_counter()

    response = await call_next(request)

    duration = round(time.perf_counter() - start_time, 4)
    # We previously used time.time(), but time.perf_counter() is a better choice for measuring execution time because it provides a high-resolution timer designed for benchmarking durations.

    logger.info(
        "%s %s | Status: %s | Time: %.4fs",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )

    return response