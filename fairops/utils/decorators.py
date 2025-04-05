def private(obj):
    """Decorator to mark methods/functions as private (excluded from Sphinx)."""
    obj.__private_api__ = True
    return obj
