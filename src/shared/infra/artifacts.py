"""Strict artifact reads and atomic writes with portable application errors."""

import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from shared.application.diagnostics import record_diagnostic
from shared.application.errors import ArtifactError, StorageError


def read_json_object(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except (OSError, ValueError, UnicodeError) as error:
        raise ArtifactError(f"Cannot read JSON artifact: {path}") from error
    if not isinstance(value, dict):
        raise ArtifactError(f"Expected a JSON object in artifact: {path}")
    return value


def atomic_write(path: Path, data: bytes) -> None:
    """Leave the previous artifact intact when writing or replacement fails."""
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(dir=path.parent, prefix=".artifact-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
        temporary.replace(path)
    except OSError as error:
        raise StorageError(f"Cannot write artifact: {path}") from error
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError as cleanup:
                record_diagnostic(f"Cannot remove temporary artifact {temporary}", cleanup)
