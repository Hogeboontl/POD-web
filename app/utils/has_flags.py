

#helper function to search button states from multiple tables.
def has_flag(*rows, attr):
    return any(getattr(r, attr, False) for r in rows if r is not None)