"""The two halves of as_gql_generic_itr's paging contract.

Both landed independently — the (items, total) early-exit and the start_skip origin — and
neither had a test. They meet in one `for skip in range(...)` line, and the interaction
between them is exactly the kind of thing that looks right and is off by a page.

Built on a bare instance so the real loop runs, following test_as_inventory_flatten's
_itr_over_pages: stubbing the loop out is what would hide a regression in it.
"""
import functools

import pytest

from sdk.as_inventory import AndromedaInventory


def _drain(pages, *, page_size=2, total=None, **itr_kwargs):
    """Page over canned data, recording the skip each call was asked for.

    ``total`` non-None makes the stub base_fn return (items, total) — the tuple shape a
    query with its own pageInfo.count uses. Left None it returns a plain list, which is
    what the other 63 call sites do.
    """
    inv = AndromedaInventory.__new__(AndromedaInventory)
    inv.default_page_size = page_size
    calls = []

    def _base_fn(size, skip):
        calls.append(skip)
        index = skip // size
        items = pages[index] if 0 <= index < len(pages) else []
        return (items, total) if total is not None else items

    partial_fn = functools.partial(_base_fn)
    # rate_limit=0: the pacing sleep is real (1s/page) and not what these assert.
    rows = list(inv.as_gql_generic_itr(
        partial_fn, page_size=page_size, rate_limit=0, **itr_kwargs))
    return rows, calls


# ---------------------------------------------------------------------------
# main's half: a total lets the loop stop exactly
# ---------------------------------------------------------------------------

def test_a_known_total_stops_without_a_trailing_probe_page():
    """The point of the tuple contract: knowing the total saves the extra round trip
    (plus its pacing sleep) that discovering the end by a short page costs."""
    pages = [[1, 2], [3, 4]]
    rows, calls = _drain(pages, page_size=2, total=4)
    assert rows == [1, 2, 3, 4]
    assert calls == [0, 2], "a third call would be the wasted round trip the total avoids"


def test_without_a_total_the_end_is_discovered_by_a_short_page():
    rows, calls = _drain([[1, 2], [3]], page_size=2)
    assert rows == [1, 2, 3]
    assert calls == [0, 2]


def test_without_a_total_an_exact_multiple_costs_one_empty_probe():
    """The cost the total avoids, pinned so the tuple path's value is visible."""
    rows, calls = _drain([[1, 2], [3, 4]], page_size=2)
    assert rows == [1, 2, 3, 4]
    assert calls == [0, 2, 4], "the empty third page is how the end is found"


def test_a_plain_list_base_fn_is_still_supported():
    rows, _ = _drain([[1], [2], [3]], page_size=1)
    assert rows == [1, 2, 3]


# ---------------------------------------------------------------------------
# my half: start_skip is a server-side origin
# ---------------------------------------------------------------------------

def test_start_skip_offsets_the_first_request_rather_than_dropping_rows():
    """Skipping client-side would re-fetch every earlier page; the offset has to reach
    the server, so the FIRST call must already carry it."""
    rows, calls = _drain([[1, 2], [3, 4], [5, 6]], page_size=2, start_skip=4)
    assert calls[0] == 4, "the first request must start at the offset, not at 0"
    assert rows == [5, 6]


def test_start_skip_defaults_to_the_beginning():
    _, calls = _drain([[1, 2], [3]], page_size=2)
    assert calls[0] == 0


def test_max_count_bounds_rows_returned_not_the_offset_reached():
    """Documented behaviour worth pinning: max_count is counted FROM start_skip, so it
    caps what this call returns rather than the absolute offset it may reach."""
    pages = [[1, 2], [3, 4], [5, 6], [7, 8]]
    rows, _ = _drain(pages, page_size=2, start_skip=4, max_count=4)
    assert rows == [5, 6, 7, 8]


# ---------------------------------------------------------------------------
# where the two halves meet
# ---------------------------------------------------------------------------

def test_a_total_is_absolute_and_start_skip_does_not_double_count_it():
    """`fetched` counts from start_skip while `total` is an absolute row count, so the
    offset reached is start_skip + fetched. A bare `fetched >= total` comparison is the
    smaller number and fires late rather than early: the ROWS stay right, but the caller
    pays the extra round trip the total was added to avoid. That makes it invisible to any
    assertion on rows alone, which is why this one counts requests."""
    pages = [[1, 2], [3, 4], [5, 6]]
    rows, calls = _drain(pages, page_size=2, start_skip=2, total=6)
    assert rows == [3, 4, 5, 6]
    assert calls == [2, 4], (
        "a bare `fetched >= total` check reaches the absolute total at skip=4 but does not "
        "notice, and spends a third request on skip=6"
    )


def test_the_total_still_ends_the_loop_when_starting_from_zero():
    rows, calls = _drain([[1, 2], [3, 4], [5, 6]], page_size=2, start_skip=0, total=4)
    assert rows == [1, 2, 3, 4]
    assert calls == [0, 2]


@pytest.mark.parametrize("start_skip", [0, 2, 4])
def test_paging_from_any_origin_reaches_the_end_of_the_data(start_skip):
    """Whatever the origin, the drain ends at the real end of the data — no page is
    skipped and none is served twice."""
    pages = [[1, 2], [3, 4], [5, 6]]
    rows, _ = _drain(pages, page_size=2, start_skip=start_skip, total=6)
    assert rows == [1, 2, 3, 4, 5, 6][start_skip:]
