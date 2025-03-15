try:
    from .version import __version__
except ImportError:
    try:
        from importlib.metadata import version
        __version__ = version("fairops")
    except ImportError:
        __version__ = "0.0.0"  # Default version if all else fails

__all__ = ["main_function", "__version__"]
