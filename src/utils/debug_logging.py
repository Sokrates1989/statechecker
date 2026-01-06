"""Module: debug_logging.py

Description:
    Debug logging utilities for the statechecker server.

    This module provides helpers for enabling detailed request logging
    when DEBUG_ENABLED is set to true in environment variables.
"""

from __future__ import annotations

import os
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


# Endpoints to skip logging (reduces noise from health checks)
SKIP_LOG_PATHS = {"/health", "/health/", "/v1/health", "/v1/health/"}


def _is_debug_enabled() -> bool:
    """Check if debug mode is enabled via environment variable.

    Returns:
        bool: True if DEBUG_ENABLED is set to a truthy value.
    """
    debug_val = os.environ.get("DEBUG_ENABLED", "false").lower()
    return debug_val in ("true", "1", "yes", "y")


async def log_request_details(request: Request, call_next: Callable) -> Response:
    """Middleware to log detailed request and response information for debugging.

    Logs request method, URL, headers, body, and response status/body.
    Skips logging for health check endpoints to reduce noise.

    Args:
        request (Request): The incoming request.
        call_next (Callable): The next middleware/handler in the chain.

    Returns:
        Response: The response from the handler.
    """
    # Skip logging for health check endpoints
    if request.url.path in SKIP_LOG_PATHS:
        return await call_next(request)

    # Log basic request info
    print(f"🔹 Received request: {request.method} {request.url}")

    # Log request headers
    headers = request.headers
    print(f"🔹 Request headers: {dict(headers)}")

    # Read and log the request body
    body = await request.body()
    print(f"🔹 Request body: {body.decode('utf-8') if body else 'No Body'}")

    response = await call_next(request)

    # Collect the response body so it can be logged and re-sent
    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk

    print(f"🟪 Response status: {response.status_code}")
    print(f"🟪 Response headers: {dict(response.headers)}")

    # Only decode text responses, skip binary content
    content_type = response.headers.get('content-type', '')
    if response_body:
        is_binary = any(binary_type in content_type.lower() for binary_type in
                        ['application/octet-stream', 'application/gzip', 'application/zip',
                         'image/', 'video/', 'audio/', 'application/pdf'])

        if is_binary:
            print(f"🟪 Response body: <Binary content, {len(response_body)} bytes>")
        else:
            try:
                print(f"🟪 Response body: {response_body.decode('utf-8')}")
            except UnicodeDecodeError:
                print(f"🟪 Response body: <Binary content, {len(response_body)} bytes>")
    else:
        print(f"🟪 Response body: No Body")

    # Rebuild the Response since body_iterator can only be consumed once
    new_response = Response(
        content=response_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
        background=response.background,
    )

    return new_response


def setup_debug_logging(app: FastAPI) -> None:
    """Configure debug logging middleware for the FastAPI application.

    This middleware is only enabled when DEBUG_ENABLED is set to true.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    if _is_debug_enabled():
        print("🔧 DEBUG_ENABLED=true: Debug logging middleware activated")
        app.add_middleware(BaseHTTPMiddleware, dispatch=log_request_details)
    else:
        print("🔧 DEBUG_ENABLED=false: Debug logging middleware skipped")
