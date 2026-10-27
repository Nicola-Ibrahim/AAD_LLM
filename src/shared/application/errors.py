"""Failures of shared IO capabilities, independent of vendor libraries."""


class StorageError(RuntimeError):
    """A required persistence operation failed; successful completion is unsafe."""


class ArtifactError(RuntimeError):
    """An existing artifact is invalid or unreadable, rather than absent."""
