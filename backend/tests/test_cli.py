import os
import subprocess
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_audit_model_resolves_without_the_api() -> None:
    """The command-line tools record audit events without importing the API.

    Regression: `python -m app.ingestion.cli` failed after its first dataset
    because the audit table's reference to staff accounts could not be resolved.
    """
    code = (
        "from sqlalchemy.orm import configure_mappers\n"
        "import app.ingestion.cli\n"
        "from app.core.audit import AuditEvent\n"
        "configure_mappers()\n"
        "[fk.column for fk in AuditEvent.__table__.foreign_keys]\n"
    )
    result = subprocess.run(  # noqa: S603 (fixed command, test only)
        [sys.executable, "-c", code], cwd=BACKEND_DIR, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
