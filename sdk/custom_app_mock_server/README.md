# Custom App Mock Server

A mock SaaS application that exposes its access inventory over paginated REST
APIs, backed by `customapp/mock_data_v3.json`. It exists so the custom app
inventory download pipeline can be exercised end-to-end without a real vendor,
and as a reference for the REST contract a real application should provide.

This package contains **only the API server**. The matching downloader is the
single uploadable file
[`../custom_app_inventory_downloader/custom_app_rest_api_downloader.py`](../custom_app_inventory_downloader/custom_app_rest_api_downloader.py),
which pages through these APIs and exports a `CustomAppInventory` JSON using
the reusable framework at `../customapp/inventorydownloader/`.

## REST API

`GET /api/{section}` for `users | nhis | groups | scopes | roles |
permissions | assignments | resources | agents`, plus `GET /health`.

Query params:

| Param | Default | Behavior |
| --- | --- | --- |
| `page` | 1 | 1-indexed page number |
| `page_size` | 20 | items per page (max 100) |
| `id` | — | exact match on the item id (name for permissions) |
| `name` | — | case-insensitive substring on `name` |
| `ids` | — | comma-separated exact-match list |

Response envelope:

```json
{"data": [...], "page": 1, "page_size": 20, "total": 95, "has_next": true}
```

## Usage

```bash
pip install -r requirements.txt

# Start the server (defaults to customapp/mock_data_v3.json)
python server.py --port 5050 [--data_file path.json] [--log_level DEBUG]

# Smoke test
curl 'http://localhost:5050/api/users?page=1&page_size=5'
curl 'http://localhost:5050/api/users?name=chip'

# Download inventory from it
python ../custom_app_inventory_downloader/custom_app_rest_api_downloader.py \
    --server http://localhost:5050 --app_name mock_app --output_dir /tmp/mock_out
```

## Layout

```text
server.py       Flask server: /health + one explicit route per model type,
                all sharing a paginated_response() helper
data_store.py   loads the mock JSON; filter + paginate queries
```
