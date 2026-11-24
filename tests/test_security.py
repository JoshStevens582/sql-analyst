import pytest

from sql_analyst.security import SqlValidationError, normalize_select_sql


def test_allows_select() -> None:
    sql = normalize_select_sql("SELECT sku FROM products LIMIT 5")
    assert "SELECT" in sql.upper()


@pytest.mark.parametrize(
    "bad",
    [
        "DELETE FROM products",
        "DROP TABLE products",
        "UPDATE products SET name = 'x'",
        "INSERT INTO products(sku,name) VALUES ('a','b')",
        "SELECT 1; DELETE FROM products",
    ],
)
def test_blocks_writes(bad: str) -> None:
    with pytest.raises(SqlValidationError):
        normalize_select_sql(bad)