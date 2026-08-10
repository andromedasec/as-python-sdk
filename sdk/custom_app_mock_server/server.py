"""Mock custom application REST server.

Serves paginated inventory APIs (backed by customapp mock data) that the
inventory downloader's generators page through. Every endpoint follows the
same shape, so copying this file is enough to stand up a server for a new
custom app:

    GET /api/{section}?page=1&page_size=20[&id=X][&name=Y][&ids=a,b]

    -> {"data": [...], "page": 1, "page_size": 20, "total": 95, "has_next": true}

Usage:
    python server.py [--port 5050] [--data_file ...] [--log_level INFO]
"""

import argparse
import logging
import sys
from pathlib import Path

# Allow running as a plain script: put lib/python on the path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# pylint: disable=wrong-import-position
from flask import Flask, jsonify, request

from sdk.custom_app_mock_server.data_store import DataStore
from sdk.customapp.inventorydownloader.logging_config import setup_logging

logger = logging.getLogger(__name__)

DEFAULT_PORT = 5050
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

app = Flask(__name__)
# Loaded with the default mock data at import; main() swaps it when --data_file is given.
data_store = DataStore()


def paginated_response(section: str):
    """Serve one page of a section, honoring the shared filter/pagination params.

    Query params: page (1-indexed), page_size (max 100), id (exact),
    name (case-insensitive substring), ids (comma-separated exact list).
    """
    try:
        page = max(int(request.args.get("page", 1)), 1)
        page_size = min(max(int(request.args.get("page_size", DEFAULT_PAGE_SIZE)), 1),
                        MAX_PAGE_SIZE)
    except ValueError:
        return jsonify({"error": "page and page_size must be integers"}), 400

    ids_arg = request.args.get("ids")
    ids = [i.strip() for i in ids_arg.split(",") if i.strip()] if ids_arg else None

    items, total = data_store.query(
        section,
        item_id=request.args.get("id"),
        name=request.args.get("name"),
        ids=ids,
        page=page,
        page_size=page_size,
    )
    return jsonify({
        "data": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_next": page * page_size < total,
    })


@app.get("/health")
def health():
    """Liveness check."""
    return jsonify({"status": "ok"})


@app.get("/api/users")
def list_users():
    """Paginated user inventory."""
    return paginated_response("users")


@app.get("/api/nhis")
def list_nhis():
    """Paginated NHI (non-human identity) inventory."""
    return paginated_response("nhis")


@app.get("/api/groups")
def list_groups():
    """Paginated group inventory."""
    return paginated_response("groups")


@app.get("/api/scopes")
def list_scopes():
    """Paginated scope inventory."""
    return paginated_response("scopes")


@app.get("/api/roles")
def list_roles():
    """Paginated role inventory."""
    return paginated_response("roles")


@app.get("/api/permissions")
def list_permissions():
    """Paginated permission inventory."""
    return paginated_response("permissions")


@app.get("/api/assignments")
def list_assignments():
    """Paginated role assignment inventory."""
    return paginated_response("assignments")


@app.get("/api/resources")
def list_resources():
    """Paginated resource inventory."""
    return paginated_response("resources")


@app.get("/api/agents")
def list_agents():
    """Paginated AI agent inventory."""
    return paginated_response("agents")


def main():
    """Parse CLI arguments and run the mock server."""
    parser = argparse.ArgumentParser(
        description="Mock custom application inventory REST server")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--data_file", default=None,
        help="Path to a customapp inventory JSON file "
             "(default: customapp/mock_data_v3.json)")
    parser.add_argument("--log_level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    setup_logging(level=args.log_level)
    if args.data_file:
        global data_store  # pylint: disable=global-statement
        data_store = DataStore(args.data_file)
    logger.info("Mock server listening on port %d", args.port)
    app.run(host="localhost", port=args.port, debug=False)


if __name__ == "__main__":
    main()
