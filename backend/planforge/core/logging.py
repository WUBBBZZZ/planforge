"""Structured logging configuration."""

import logging


def configure_logging(level: str = "INFO") -> None:
    """Configure application-wide logging.

    Logs must never include request bodies, passwords, tokens, cookies,
    session identifiers, planner content, or personal data.
    """
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    # Reduce noise from third-party libraries in development.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
