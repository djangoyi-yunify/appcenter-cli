"""Output formatting for the AppCenter CLI.

Default output is pretty-printed JSON (best for AI agents). A
human-readable table view is available via ``--output table``.
"""

import json


def print_json(data) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def _cell(value, width):
    text = "" if value is None else str(value)
    if len(text) > width:
        text = text[: width - 1] + "…"
    return text.ljust(width)


def print_table(rows, columns=None) -> None:
    """Print a list of dicts as an aligned table.

    Args:
        rows: list of dicts.
        columns: ordered list of column keys. If None, derived from the
            union of keys across rows.
    """
    if not rows:
        print("(no results)")
        return
    if columns is None:
        columns = []
        for row in rows:
            for key in row.keys():
                if key not in columns:
                    columns.append(key)
    widths = {col: len(col) for col in columns}
    for row in rows:
        for col in columns:
            text = "" if row.get(col) is None else str(row.get(col))
            widths[col] = max(widths[col], min(len(text), 40))
    header = "  ".join(_cell(col, widths[col]) for col in columns)
    print(header)
    print("  ".join("-" * widths[col] for col in columns))
    for row in rows:
        print("  ".join(_cell(row.get(col), widths[col]) for col in columns))


def render(data, output: str, table_columns=None) -> None:
    """Render a response dict according to the output mode.

    Args:
        data: the API response dict.
        output: "json" or "table".
        table_columns: optional column keys for table mode.
    """
    if output == "table":
        if isinstance(data, list):
            print_table(data, table_columns)
        elif isinstance(data, dict):
            # Find the first list-valued field as the table body.
            for value in data.values():
                if isinstance(value, list) and value and isinstance(value[0], dict):
                    print_table(value, table_columns)
                    return
            print_table([data], table_columns)
        else:
            print(data)
    else:
        print_json(data)
