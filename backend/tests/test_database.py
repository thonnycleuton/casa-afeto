from sqlalchemy import text
from app.core.database import Base, engine


def test_m1_tables_in_metadata() -> None:
    """Verify M1 defines only the approved product and inventory tables."""
    assert set(Base.metadata.tables) == {"products", "inventory_movements"}


def test_database_connection() -> None:
    """Verify that SQLAlchemy engine can successfully connect and execute a basic query."""
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar()
        assert result == 1
