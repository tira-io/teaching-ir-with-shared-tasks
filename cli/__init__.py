from importlib.metadata import PackageNotFoundError, version

# Try to determine package version.
try:
    __version__ = version("teaching-ir-with-shared-tasks")
except PackageNotFoundError:
    __version__ = "unknown"
