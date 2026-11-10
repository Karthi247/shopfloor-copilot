import re
from datetime import datetime


def _effective_date(value):
    if not value or value == "Unknown":
        return None
    for fmt in ("%d-%b-%Y", "%d-%B-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            pass
    return None


def latest_revision(records):
    revisions = {}
    for item in records:
        if item.get("revision_known"):
            revision = item["revision"]
            date = _effective_date(item.get("effective_date"))
            if revision not in revisions or (
                date and (not revisions[revision] or date > revisions[revision])
            ):
                revisions[revision] = date
    if not revisions:
        return None
    if all(date is not None for date in revisions.values()):
        return max(revisions, key=lambda revision: (revisions[revision], revision))
    return max(revisions)


def select_revisions(hits, question):
    requested = {
        int(match.group(1))
        for match in re.finditer(r"\b(?:rev(?:ision)?\s*)0?(\d+)\b", question, re.I)
    }
    groups = {}
    for hit in hits:
        if hit["document_number"] != "UNKNOWN":
            groups.setdefault(hit["document_number"], []).append(hit)
    chosen = []
    for hit in hits:
        group = groups.get(hit["document_number"], [])
        newest = latest_revision(group)
        if requested:
            if hit["revision_known"] and hit["revision"] in requested:
                chosen.append(hit)
        elif newest is not None and hit["revision_known"] and hit["revision"] != newest:
            continue
        else:
            chosen.append(hit)
    return sorted(chosen, key=lambda item: item["distance"])
