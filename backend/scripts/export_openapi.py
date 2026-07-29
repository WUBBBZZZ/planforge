"""Export the FastAPI OpenAPI schema to a JSON file for frontend type generation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def export_openapi(output_path: Path) -> None:
    from planforge.main import create_app

    app = create_app()
    schema = app.openapi()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(schema, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_output = (
        Path(__file__).resolve().parents[2] / "frontend" / "openapi" / "openapi.json"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help="Destination JSON file",
    )
    args = parser.parse_args(argv)

    export_openapi(args.output.resolve())
    print(f"Wrote OpenAPI schema to {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
