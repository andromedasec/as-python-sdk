# AI Coding Prompt: Custom App Inventory Downloader framework + Mock Server

## Task: Custom App Inventory Downloader framework + Mock Server — Phase 1

### Background

Andromeda's custom app SDK is at `lib/python/sdk/customapp/`. Read these first:

- `customapp/custom_app_models.py` — V2 dataclasses (CustomAppUserV2 etc.), CustomAppInventory,
  load_inventory_from_json, validate_inventory_consistency
- `customapp/custom_app_utils.py` — convert_to_andromeda_dict
- `customapp/mock_data_v3.json` — mock inventory data (sections: users, nhis, groups, scopes,
  roles, permissions, assignments, resources, agents)

Use ONLY the V2 models (snake_case). Never use the deprecated camelCase wrapper classes.

### Part A: Core package — `lib/python/sdk/customapp/inventorydownloader/`

A reusable, HTTP-agnostic downloader framework:

1. `model_types.py` — ModelType enum (USERS..AGENTS) + metadata: CustomAppInventory attribute
   name and key function per type (users/nhis keyed by username, permissions by name, rest by id)
2. `filters.py` — InventoryFilter dataclass: id (exact), name (substring), ids (list of exact)
3. `registry.py` — InventoryGeneratorRegistry with register(model_type, fn) and a decorator form.
   Generator contract: `fn(filters: InventoryFilter, offset: int = 0) -> Iterator[V2Model]`.
   The offset is the count of already-consumed items; the generator must resume from there.
   Generators may yield `ItemError(item_id, error)` for a per-item transform failure so the
   core can audit the failure and continue.
4. `progress_tracker.py` — checkpoint at `{output_dir}/.progress.json` with per-model
   status (pending/in_progress/completed) + items_consumed/succeeded/failed; partial item dicts
   persisted to `{output_dir}/.partial/{model}.json` so restarts reload data and resume
   generators at offset.
5. `logging_config.py` —
   - `setup_logging(level: str, log_dir: str)`: configures the ROOT logger (so every module
     logger inherits the level) with a console handler and a rotating file handler at
     `{log_dir}/downloader.log`. Default level INFO; DEBUG shows page fetches, offsets,
     checkpoint writes.
   - `get_audit_logger(log_dir)`: named logger "customapp.audit" (propagate=False) writing
     `{log_dir}/inventory_audit.log`. One line per item outcome:

     ```text
     AUDIT <model> CREATE_SUCCESS id=<key>
     AUDIT <model> CREATE_FAILURE id=<key> error="<exception message>"
     ```

     plus MODEL_STARTED / MODEL_RESUMED offset=N / MODEL_COMPLETED total= success= failure=,
     EXPORT_SUCCESS file=..., EXPORT_FAILURE error=..., VALIDATION_ERRORS count=... details.
6. `downloader.py` — `BaseInventoryDownloader(app_name, registry, output_dir)`:
   - `download()`: iterate registered types, skip completed, resume in_progress at offset,
     checkpoint every 100 items; wrap each item consume in try/except — audit CREATE_FAILURE
     with the error and continue (never abort batch); audit CREATE_SUCCESS per item;
     debug-log each page/offset step. On a generator crash, checkpoint before re-raising so
     the next run resumes.
   - `export()`: validate_inventory_consistency (audit VALIDATION_ERRORS if any), then
     asdict + convert_to_andromeda_dict and write `{output_dir}/{app_name}-{timestamp}.json`
     (audit EXPORT_SUCCESS/EXPORT_FAILURE). Clear the checkpoint after a successful export.
   - `run(reset=False)`: optional checkpoint reset, then download + export

### Part B: Mock server — `lib/python/sdk/custom_app_mock_server/` (User model only)

Contains ONLY the API server (no downloader code, no Flask blueprints — keep the
routes explicit and copy-friendly):

1. `data_store.py` — load mock_data_v3.json; query(section, item_id, name, ids, page, page_size)
2. `server.py` — Flask app with GET /health and one explicit GET /api/users route calling a
   shared paginated_response(section) helper. Envelope:
   `{"data", "page", "page_size", "total", "has_next"}`. Params: page (default 1),
   page_size (default 20, max 100), id, name, ids (comma-separated)
3. `requirements.txt` — flask, requests

### Part C: Single-file downloader

Path: `lib/python/sdk/custom_app_inventory_downloader/custom_app_rest_api_downloader.py`

One self-contained .py file, uploadable to Andromeda as
INVENTORY_DOWNLOADER_FILE_PYTHON (all downloader-side code lives here, none in the
mock server package):

1. `RestApiClient` — fetch_page(resource, page, page_size, item_id=None, name=None, ids=None);
   all HTTP calls live here
2. Plain `transform_user(raw) -> CustomAppUserV2` function (passthrough; construct nested
   CustomAppUserHRISAttributes when present)
3. `registry` + `_paged_generator(resource, transform_fn)` closure paging through /api/users,
   honoring offset for resume
4. `main()` — CLI (--server, --app_name, --output_dir, --reset, --models, --filter_id,
   --filter_name, --filter_ids, --page_size, --log_level [default INFO], --log_dir [default
   {output_dir}/logs]); calls setup_logging first, then wires registry into
   BaseInventoryDownloader.run(). Server URL / page_size fall back to the
   AS_CUSTOM_APP_METADATA env JSON ({"server_url": ..., "page_size": ...}) when the
   args are not given (uploaded-execution convention)

### Acceptance (Phase 1)

- `curl 'http://localhost:5050/api/users?page=1&page_size=5'` returns 5 users + envelope
- `curl 'http://localhost:5050/api/users?name=<substring>'` filters correctly
- main.py produces a validated users-only inventory JSON
- Kill main.py mid-download, rerun: resumes from checkpoint (audit shows MODEL_RESUMED);
  --reset restarts from scratch
- `{log_dir}/inventory_audit.log` has one CREATE_SUCCESS/CREATE_FAILURE line per user,
  failures include the error message
- `--log_level DEBUG` shows per-page fetch/checkpoint detail; default INFO stays quiet

### Phase 2 (after Phase 1 works)

Add nhis, groups, scopes, roles, permissions — 5 explicit server routes, 5 passthrough
transform functions, 5 generator registrations. Core stays untouched.

### Phase 3

Add assignments, resources, agents; then a full-inventory run whose output passes
validate_inventory_consistency with zero errors and loads via load_inventory_from_json.
