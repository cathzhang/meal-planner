"""
交互式录入新菜品，追加到 data/recipes.json

用法:
    python add_recipe.py

流程:
    1. 一问一答，提示输入每个字段
    2. 自动追加到 data/recipes.json
    3. 可选：同时更新数据库
"""

import json
import os
from models import DishType, Difficulty, SpicyLevel, PriceLevel
from db import insert_dish
from models import Dish

JSON_PATH = "data/recipes.json"


def input_choice(prompt: str, options: list[str]) -> str:
    """让用户从选项中选择一个"""
    print(f"\n{prompt}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    while True:
        try:
            idx = int(input("请选择编号: ").strip())
            if 1 <= idx <= len(options):
                return options[idx - 1]
        except ValueError:
            pass
        print("输入无效，请重新选择")


def input_bool(prompt: str) -> bool:
    """输入是/否"""
    while True:
        val = input(f"{prompt} (y/n): ").strip().lower()
        if val in ("y", "yes", "是", "1"):
            return True
        if val in ("n", "no", "否", "0"):
            return False
        print("请输入 y 或 n")


def input_list(prompt: str) -> list[str]:
    """输入逗号分隔的列表"""
    val = input(f"{prompt} (多个用逗号分隔，没有则直接回车): ").strip()
    if not val:
        return []
    return [x.strip() for x in val.split(",") if x.strip()]


def input_int(prompt: str) -> int:
    """输入正整数"""
    while True:
        try:
            return int(input(f"{prompt}: ").strip())
        except ValueError:
            print("请输入数字")


def input_optional_str(prompt: str) -> str | None:
    """输入字符串，空则返回 None"""
    val = input(f"{prompt} (没有则直接回车): ").strip()
    return val if val else None


def collect_dish() -> dict:
    """交互式收集一道菜的信息"""
    print("=" * 40)
    print("录入新菜品")
    print("=" * 40)

    dish = {}
    dish["name"] = input("菜名: ").strip()

    dish["ingredients"] = input_list("食材（如：番茄, 鸡蛋）")
    dish["sauces"] = input_list("特殊酱料（如：番茄酱, 蚝油）")

    dish["cook_time_minutes"] = input_int("灶上制作时间（分钟）")
    dish["prep_time_minutes"] = input_int("备菜时间（分钟，切配腌制等）")

    dish["difficulty"] = input_choice(
        "难易程度", ["简单", "中等", "困难"]
    )
    dish["dish_type"] = input_choice(
        "菜品类型", ["大荤", "小荤", "全素"]
    )

    dish["summer_recommended"] = input_bool("夏日推荐？")
    dish["winter_recommended"] = input_bool("冬日推荐？")

    dish["spicy_level"] = input_choice(
        "辣味", ["不辣", "可免辣", "辣"]
    )
    dish["kid_friendly"] = input_bool("儿童友好？")

    months = input("适合月份（如 3,4,5，全年则直接回车）: ").strip()
    dish["seasonal_months"] = [int(m.strip()) for m in months.split(",") if m.strip()] if months else []

    dish["price_level"] = input_choice(
        "菜价评估", ["便宜", "中等", "较贵"]
    )
    dish["has_prepackaged"] = input_bool("是否有成熟预制菜？")
    dish["is_soup"] = input_bool("是否是汤菜？")
    dish["variant_group"] = input_optional_str("变体组（如：排骨汤系列）")
    dish["liked_by"] = input_list("谁喜欢（如：爸爸, 妈妈, 孩子）")

    return dish


def append_to_json(dish: dict) -> None:
    """追加到 JSON 文件"""
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    # 检查是否已存在
    for existing in data:
        if existing["name"] == dish["name"]:
            print(f"⚠️  {dish['name']} 已存在，跳过追加")
            return

    data.append(dish)

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 已追加到 {JSON_PATH}")


def add_to_db(dish: dict) -> None:
    """同时插入数据库"""
    d = Dish(
        name=dish["name"],
        ingredients=dish["ingredients"],
        sauces=dish["sauces"],
        cook_time_minutes=dish["cook_time_minutes"],
        prep_time_minutes=dish["prep_time_minutes"],
        difficulty=Difficulty(dish["difficulty"]),
        dish_type=DishType(dish["dish_type"]),
        summer_recommended=dish["summer_recommended"],
        winter_recommended=dish["winter_recommended"],
        spicy_level=SpicyLevel(dish["spicy_level"]),
        kid_friendly=dish["kid_friendly"],
        seasonal_months=dish["seasonal_months"],
        price_level=PriceLevel(dish["price_level"]),
        has_prepackaged=dish["has_prepackaged"],
        is_soup=dish["is_soup"],
        variant_group=dish["variant_group"],
        liked_by=dish["liked_by"],
    )
    if insert_dish(d):
        print(f"✅ 已插入数据库")
    else:
        print(f"⚠️ 数据库中已存在 {dish['name']}，跳过")


if __name__ == "__main__":
    dish = collect_dish()
    print("\n" + "=" * 40)
    print("预览录入内容:")
    print(json.dumps(dish, ensure_ascii=False, indent=2))
    print("=" * 40)

    if input_bool("确认保存？"):
        append_to_json(dish)
        if input_bool("同时更新数据库？"):
            add_to_db(dish)
        print("\n🎉 录入完成！记得 git commit 你的数据文件")
    else:
        print("已取消")
