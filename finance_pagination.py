"""Bounded pagination for Cora read-only collections. No financial writes."""
def collect_pages(query, start, end, key, page_size, max_pages=100):
    records = []
    seen = set()
    for page in range(1, max_pages + 1):
        response = query(start, end, page=page)
        if not isinstance(response, dict) or not isinstance(response.get(key), list):
            raise ValueError("Unexpected collection schema")
        rows = response[key]
        if len(rows) > page_size:
            raise ValueError("Unexpected page size")
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"]:
                raise ValueError("Missing record identity")
            if row["id"] in seen:
                raise ValueError("Duplicate identity or repeated page")
            seen.add(row["id"])
            records.append(row)
        if len(rows) < page_size:
            return records
    raise ValueError("Pagination limit reached")
