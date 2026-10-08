from sqlalchemy import text
from app.core.database import Base, engine


def test_m1_and_m2_tables_in_metadata() -> None:
    """Verify the current product, inventory, basket, and template schema."""
    assert set(Base.metadata.tables) == {
        "products",
        "inventory_movements",
        "basket_templates",
        "basket_template_items",
        "baskets",
        "basket_items",
    }


def test_database_connection() -> None:
    """Verify that SQLAlchemy engine can successfully connect and execute a basic query."""
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar()
        assert result == 1
