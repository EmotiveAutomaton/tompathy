"""Prequential targets can use only observations resolved strictly before opening."""


def prequential(cases):
    rows = sorted(cases, key=lambda r: (r.opened, r.id))
    if len({r.id for r in rows}) != len(rows):
        raise ValueError("Duplicate evaluation targets")
    for target in rows:
        yield target, [r for r in rows if r.resolved < target.opened]
