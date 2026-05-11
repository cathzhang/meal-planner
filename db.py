import sqlite3
import json
from typing import List, Optional
from models import Dish, DISH_DATABASE, DishType, Difficulty, SpicyLevel, PriceLevel

DB_PATH = "meal_planner.db"


def init_db() -> None:
    """初始化数据库：建表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dishes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            cook_time_minutes INTEGER NOT NULL,
            prep_time_minutes INTEGER NOT NULL,
            difficulty TEXT NOT NULL,
            dish_type TEXT NOT NULL,
            summer_recommended INTEGER NOT NULL DEFAULT 0,
            winter_recommended INTEGER NOT NULL DEFAULT 0,
            spicy_level TEXT NOT NULL DEFAULT '不辣',
            kid_friendly INTEGER NOT NULL DEFAULT 0,
            price_level TEXT NOT NULL DEFAULT '中等',
            has_prepackaged INTEGER NOT NULL DEFAULT 0,
            is_soup INTEGER NOT NULL DEFAULT 0,
            variant_group TEXT,
            ingredients TEXT NOT NULL,       -- JSON array
            sauces TEXT NOT NULL,            -- JSON array
            seasonal_months TEXT NOT NULL,   -- JSON array
            liked_by TEXT NOT NULL           -- JSON array
        )
    """)

    conn.commit()
    conn.close()


def _dish_to_row(dish: Dish) -> tuple:
    """将 Dish 对象转换为数据库行元组"""
    return (
        dish.name,
        dish.cook_time_minutes,
        dish.prep_time_minutes,
        dish.difficulty.value,
        dish.dish_type.value,
        1 if dish.summer_recommended else 0,
        1 if dish.winter_recommended else 0,
        dish.spicy_level.value,
        1 if dish.kid_friendly else 0,
        dish.price_level.value,
        1 if dish.has_prepackaged else 0,
        1 if dish.is_soup else 0,
        dish.variant_group,
        json.dumps(dish.ingredients, ensure_ascii=False),
        json.dumps(dish.sauces, ensure_ascii=False),
        json.dumps(dish.seasonal_months, ensure_ascii=False),
        json.dumps(dish.liked_by, ensure_ascii=False),
    )


def _row_to_dish(row: sqlite3.Row) -> Dish:
    """将数据库行转换为 Dish 对象"""
    return Dish(
        name=row["name"],
        ingredients=json.loads(row["ingredients"]),
        sauces=json.loads(row["sauges"]) if "sauges" in row.keys() else json.loads(row["sauces"]),
        cook_time_minutes=row["cook_time_minutes"],
        prep_time_minutes=row["prep_time_minutes"],
        difficulty=Difficulty(row["difficulty"]),
        dish_type=DishType(row["dish_type"]),
        summer_recommended=bool(row["summer_recommended"]),
        winter_recommended=bool(row["winter_recommended"]),
        liked_by=json.loads(row["liked_by"]),
        spicy_level=SpicyLevel(row["spicy_level"]),
        kid_friendly=bool(row["kid_friendly"]),
        seasonal_months=json.loads(row["seasonal_months"]),
        price_level=PriceLevel(row["price_level"]),
        has_prepackaged=bool(row["has_prepackaged"]),
        is_soup=bool(row["is_soup"]),
        variant_group=row["variant_group"],
    )


def insert_dish(dish: Dish) -> bool:
    """插入单个菜品，如果已存在则跳过，返回是否成功插入"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO dishes (
                name, cook_time_minutes, prep_time_minutes, difficulty, dish_type,
                summer_recommended, winter_recommended, spicy_level, kid_friendly,
                price_level, has_prepackaged, is_soup, variant_group,
                ingredients, sauces, seasonal_months, liked_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, _dish_to_row(dish))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # 菜名已存在
        return False
    finally:
        conn.close()


def insert_dishes(dishes: List[Dish]) -> int:
    """批量插入菜品，返回成功插入的数量"""
    count = 0
    for dish in dishes:
        if insert_dish(dish):
            count += 1
    return count


def get_all_dishes() -> List[Dish]:
    """获取所有菜品"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dishes")
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_dish(row) for row in rows]


def get_dish_by_name(name: str) -> Optional[Dish]:
    """按菜名查找单个菜品"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dishes WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return _row_to_dish(row)
    return None


def get_dishes_by_variant_group(group: str) -> List[Dish]:
    """按变体组查找所有相关菜品"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dishes WHERE variant_group = ?", (group,))
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_dish(row) for row in rows]


def get_dish_names() -> List[str]:
    """只获取所有菜名列表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM dishes ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


def init_data_from_models() -> int:
    """把 models.py 里的示例数据导入数据库"""
    return insert_dishes(DISH_DATABASE)


if __name__ == "__main__":
    init_db()
    inserted = init_data_from_models()
    print(f"数据库初始化完成，成功导入 {inserted} 道菜品")

    # 简单验证
    all_names = get_dish_names()
    print(f"数据库中共有 {len(all_names)} 道菜")
    print(f"菜名列表: {all_names}")

    # 测试变体组查询
    variants = get_dishes_by_variant_group("排骨汤系列")
    print(f"\n排骨汤系列变体: {[d.name for d in variants]}")
