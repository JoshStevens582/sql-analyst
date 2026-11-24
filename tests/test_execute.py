from pathlib import Path

from sql_analyst.execute import run_select


def test_run_select_on_demo(demo_db: Path) -> None:
    columns, rows = run_select(
        "SELECT COUNT(*) AS n FROM products",
        demo_db,
        max_rows=10,
    )
    assert columns == ["n"]
    assert rows[0][0] == 4