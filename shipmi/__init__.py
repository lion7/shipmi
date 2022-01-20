from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("shipmi")
except PackageNotFoundError:
    # package is not installed
    pass
