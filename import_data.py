"""
从 data/recipes.json 重建 SQLite 数据库

用法:
    python import_data.py

说明:
    - 会先清空 dishes 表，然后重新导入
    - 数据源头永远是 data/recipes.json（文本，git 追踪）
    - meal_planner.db 是运行时生成的，不加入 git
"""

import json
from db import init_db, insert_dish
from models import Dish, DishType, Difficulty, SpicyLevel, PriceLevel
import sqlite3

JSON_PATH = "data/recipes.json"
DB_PATH = "meal_planner.db"


def load_dishes_from_json() -> list[Dish]:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    dishes = []
    for item in data:
        dishes.append(Dish(
            name=item["name"],
            ingredients=item["ingredients"],
            sauces=item["sauces"],
            cook_time_minutes=item["cook_time_minutes"],
            prep_time_minutes=item["prep_time_minutes"],
            difficulty=Difficulty(item["difficulty"]),
            dish_type=DishType(item["dish_type"]),
            summer_recommended=item["summer_recommended"],
            winter_recommended=item["winter_recommended"],
            spicy_level=SpicyLevel(item["spicy_level"]),
            kid_friendly=item["kid_friendly"],
            seasonal_months=item.get("seasonal_months", []),
            price_level=PriceLevel(item["price_level"]),
            has_prepackaged=item["has_prepackaged"],
            is_soup=item.get("is_soup", False),
            variant_group=item.get("variant_group"),
            liked_by=item.get("liked_by", []),
        ))
    return dishes


def rebuild_db() -> int:
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM dishes")
    conn.commit()
    conn.close()

    dishes = load_dishes_from_json()
    count = 0
    for dish in dishes:
        if insert_dish(dish):
            count += 1
    return count


if __name__ == "__main__":
    count = rebuild_db()
    print(f"数据库重建完成，从 {JSON_PATH} 导入了 {count} 道菜品")
