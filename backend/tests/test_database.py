from sqlalchemy import text
from app.core.database import Base, engine


def test_no_business_tables_in_metadata() -> None:
    """M0 requirement: verify that no business entities/tables are defined in ORM Base metadata."""
    assert len(Base.metadata.tables) == 0, (
        f"M0 must not introduce business tables, but found: {list(Base.metadata.tables.keys())}"
    )


def test_database_connection() -> None:
    """Verify that SQLAlchemy engine can successfully connect and execute a basic query."""
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar()
        assert result == 1
