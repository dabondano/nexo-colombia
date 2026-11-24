import pytest

from app.core.config import Settings


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        (
            "postgresql://u:p@ep-x.us-east-1.aws.neon.tech/nexo?sslmode=require",
            "postgresql+psycopg://u:p@ep-x.us-east-1.aws.neon.tech/nexo?sslmode=require",
        ),
        ("postgres://u:p@host/nexo", "postgresql+psycopg://u:p@host/nexo"),
        ("postgresql+psycopg://u:p@host/nexo", "postgresql+psycopg://u:p@host/nexo"),
    ],
)
def test_database_url_gets_the_psycopg_driver(given: str, expected: str) -> None:
    assert Settings(database_url=given).database_url == expected
