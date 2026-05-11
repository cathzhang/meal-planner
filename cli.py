#!/usr/bin/env python3
"""
菜品数据命令行管理工具

用法示例:
    python cli.py list                    # 列出所有菜
    python cli.py list --group 排骨汤系列  # 列出某变体组
    python cli.py show 番茄炒蛋            # 查看单道菜详情
    python cli.py search 排骨              # 按菜名或食材搜索
    python cli.py add                     # 交互式新增菜品
    python cli.py edit 番茄炒蛋            # 编辑菜品
    python cli.py delete 测试菜            # 删除菜品
    python cli.py stats                   # 数据统计
"""

import argparse
import json
import sys
from typing import Optional

from db import (
    init_db,
    get_all_dishes,
    get_dish_by_name,
    get_dishes_by_variant_group,
    get_dish_names,
    insert_dish,
    DB_PATH,
)
from models import (
    Dish,
    DishType,
    Difficulty,
    SpicyLevel,
    PriceLevel,
)
from add_recipe import collect_dish, append_to_json
import sqlite3

JSON_PATH = "data/recipes.json"


def _fmt_bool(val: bool) -> str:
    return "✓" if val else "✗"


def _fmt_list(items: list[str]) -> str:
    return ", ".join(items) if items else "-"


def _fmt_months(months: list[int]) -> str:
    return ", ".join(f"{m}月" for m in months) if months else "全年"


def print_dish_detail(dish: Dish) -> None:
    """打印单道菜详情"""
    print(f"\n{'=' * 50}")
    print(f"📋 {dish.name}")
    print(f"{'=' * 50}")
    print(f"  类型:       {dish.dish_type.value}")
    print(f"  难度:       {dish.difficulty.value}")
    print(f"  备菜时间:   {dish.prep_time_minutes} 分钟")
    print(f"  制作时间:   {dish.cook_time_minutes} 分钟")
    print(f"  总耗时:     {dish.total_time} 分钟")
    print(f"  辣味:       {dish.spicy_level.value}")
    print(f"  儿童友好:   {_fmt_bool(dish.kid_friendly)}")
    print(f"  夏日推荐:   {_fmt_bool(dish.summer_recommended)}")
    print(f"  冬日推荐:   {_fmt_bool(dish.winter_recommended)}")
    print(f"  适合月份:   {_fmt_months(dish.seasonal_months)}")
    print(f"  菜价:       {dish.price_level.value}")
    print(f"  预制菜:     {_fmt_bool(dish.has_prepackaged)}")
    print(f"  变体组:     {dish.variant_group or '-'}")
    print(f"  食材:       {_fmt_list(dish.ingredients)}")
    print(f"  酱料:       {_fmt_list(dish.sauces)}")
    print(f"  喜好人员:   {_fmt_list(dish.liked_by)}")
    print(f"{'=' * 50}\n")


def print_dish_table(dishes: list[Dish], title: str = "菜品列表") -> None:
    """打印菜品表格"""
    if not dishes:
        print("暂无数据")
        return

    print(f"\n📑 {title} (共 {len(dishes)} 道)")
    print("-" * 90)
    print(f"{'菜名':<10} {'类型':<6} {'难度':<6} {'备菜':>4} {'制作':>4} {'总':>4} {'辣味':<6} {'菜价':<6} {'季节':<10} {'变体组'}")
    print("-" * 90)
    for d in dishes:
        season = "夏" if d.summer_recommended else ""
        season += "冬" if d.winter_recommended else ""
        season = season or "-"
        group = d.variant_group or "-"
        print(
            f"{d.name:<10} {d.dish_type.value:<6} {d.difficulty.value:<6} "
            f"{d.prep_time_minutes:>4} {d.cook_time_minutes:>4} {d.total_time:>4} "
            f"{d.spicy_level.value:<6} {d.price_level.value:<6} {season:<10} {group}"
        )
    print("-" * 90)
    print()


def cmd_list(args: argparse.Namespace) -> None:
    """列出菜品"""
    init_db()
    if args.group:
        dishes = get_dishes_by_variant_group(args.group)
        print_dish_table(dishes, f"变体组: {args.group}")
    else:
        dishes = get_all_dishes()
        print_dish_table(dishes)


def cmd_show(args: argparse.Namespace) -> None:
    """查看单道菜"""
    init_db()
    dish = get_dish_by_name(args.name)
    if dish:
        print_dish_detail(dish)
    else:
        print(f"❌ 未找到: {args.name}")
        # 提示相似菜名
        names = get_dish_names()
        similar = [n for n in names if args.name in n or n in args.name]
        if similar:
            print(f"   你是不是想找: {', '.join(similar)}")


def cmd_search(args: argparse.Namespace) -> None:
    """搜索菜品"""
    init_db()
    keyword = args.keyword
    dishes = get_all_dishes()
    results = []
    for d in dishes:
        # 搜索菜名、食材、酱料、变体组、喜好人员
        text = f"{d.name} {' '.join(d.ingredients)} {' '.join(d.sauces)} {d.variant_group or ''} {' '.join(d.liked_by)}"
        if keyword in text:
            results.append(d)
    print_dish_table(results, f"搜索 '{keyword}' 的结果")


def cmd_add(args: argparse.Namespace) -> None:
    """新增菜品"""
    dish_dict = collect_dish()
    print("\n" + "=" * 40)
    print("预览录入内容:")
    print(json.dumps(dish_dict, ensure_ascii=False, indent=2))
    print("=" * 40)

    confirm = input("确认保存？ (y/n): ").strip().lower()
    if confirm in ("y", "yes", "是"):
        append_to_json(dish_dict)
        # 同步到数据库
        d = Dish(
            name=dish_dict["name"],
            ingredients=dish_dict["ingredients"],
            sauces=dish_dict["sauces"],
            cook_time_minutes=dish_dict["cook_time_minutes"],
            prep_time_minutes=dish_dict["prep_time_minutes"],
            difficulty=Difficulty(dish_dict["difficulty"]),
            dish_type=DishType(dish_dict["dish_type"]),
            summer_recommended=dish_dict["summer_recommended"],
            winter_recommended=dish_dict["winter_recommended"],
            spicy_level=SpicyLevel(dish_dict["spicy_level"]),
            kid_friendly=dish_dict["kid_friendly"],
            seasonal_months=dish_dict["seasonal_months"],
            price_level=PriceLevel(dish_dict["price_level"]),
            has_prepackaged=dish_dict["has_prepackaged"],
            variant_group=dish_dict["variant_group"],
            liked_by=dish_dict["liked_by"],
        )
        if insert_dish(d):
            print(f"✅ 已保存到 JSON 和数据库")
            print("📝 记得执行: git add data/recipes.json && git commit -m 'Add ...'")
        else:
            print(f"⚠️ 数据库中已存在，但 JSON 已更新")
    else:
        print("已取消")


def cmd_edit(args: argparse.Namespace) -> None:
    """编辑菜品"""
    init_db()
    old_dish = get_dish_by_name(args.name)
    if not old_dish:
        print(f"❌ 未找到: {args.name}")
        return

    print("当前内容:")
    print_dish_detail(old_dish)
    print("请输入新值（直接回车保持原值）\n")

    # 读取 JSON
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 找到要编辑的条目
    target = None
    for item in data:
        if item["name"] == args.name:
            target = item
            break

    if not target:
        print("❌ JSON 中未找到该菜品")
        return

    # 逐字段编辑
    def edit_field(key: str, current, transform=str):
        prompt = f"{key} [{current}]: "
        val = input(prompt).strip()
        return transform(val) if val else current

    def edit_list(key: str, current: list[str]) -> list[str]:
        val = input(f"{key} [{', '.join(current)}] (逗号分隔): ").strip()
        return [x.strip() for x in val.split(",") if x.strip()] if val else current

    def edit_bool(key: str, current: bool) -> bool:
        val = input(f"{key} [{'y' if current else 'n'}]: ").strip().lower()
        if val in ("y", "yes", "是", "1"):
            return True
        if val in ("n", "no", "否", "0"):
            return False
        return current

    target["name"] = edit_field("菜名", target["name"])
    target["ingredients"] = edit_list("食材", target["ingredients"])
    target["sauces"] = edit_list("酱料", target["sauces"])
    target["cook_time_minutes"] = edit_field("制作时间", target["cook_time_minutes"], int)
    target["prep_time_minutes"] = edit_field("备菜时间", target["prep_time_minutes"], int)

    diff_opts = ["简单", "中等", "困难"]
    print(f"难度选项: {', '.join(diff_opts)}")
    target["difficulty"] = edit_field("难度", target["difficulty"])

    type_opts = ["大荤", "小荤", "全素"]
    print(f"类型选项: {', '.join(type_opts)}")
    target["dish_type"] = edit_field("类型", target["dish_type"])

    target["summer_recommended"] = edit_bool("夏日推荐", target["summer_recommended"])
    target["winter_recommended"] = edit_bool("冬日推荐", target["winter_recommended"])

    spicy_opts = ["不辣", "可免辣", "辣"]
    print(f"辣味选项: {', '.join(spicy_opts)}")
    target["spicy_level"] = edit_field("辣味", target["spicy_level"])

    target["kid_friendly"] = edit_bool("儿童友好", target["kid_friendly"])

    months = edit_field("适合月份(逗号分隔)", ", ".join(str(m) for m in target.get("seasonal_months", [])), str)
    target["seasonal_months"] = [int(m.strip()) for m in months.split(",") if m.strip()] if months else []

    price_opts = ["便宜", "中等", "较贵"]
    print(f"菜价选项: {', '.join(price_opts)}")
    target["price_level"] = edit_field("菜价", target["price_level"])

    target["has_prepackaged"] = edit_bool("预制菜", target["has_prepackaged"])

    vg = edit_field("变体组", target.get("variant_group") or "")
    target["variant_group"] = vg if vg else None

    target["liked_by"] = edit_list("喜好人员", target.get("liked_by", []))

    # 写回 JSON
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 重建数据库
    from import_data import rebuild_db
    rebuild_db()

    print(f"\n✅ 已更新 {args.name}")
    print("📝 记得执行: git add data/recipes.json && git commit -m 'Update ...'")


def cmd_delete(args: argparse.Namespace) -> None:
    """删除菜品"""
    # 先读 JSON
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    original_len = len(data)
    data = [d for d in data if d["name"] != args.name]

    if len(data) == original_len:
        print(f"❌ 未找到: {args.name}")
        return

    confirm = input(f"确定删除 '{args.name}'？ (y/n): ").strip().lower()
    if confirm not in ("y", "yes", "是"):
        print("已取消")
        return

    # 写回 JSON
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 重建数据库
    from import_data import rebuild_db
    rebuild_db()

    print(f"✅ 已删除 {args.name}")
    print("📝 记得执行: git add data/recipes.json && git commit -m 'Delete ...'")


def cmd_stats(args: argparse.Namespace) -> None:
    """数据统计"""
    init_db()
    dishes = get_all_dishes()

    print(f"\n📊 数据统计")
    print(f"{'=' * 40}")
    print(f"  总菜品数:   {len(dishes)}")

    type_counts = {}
    diff_counts = {}
    price_counts = {}
    spicy_counts = {}
    variant_groups = set()
    seasonal = 0
    kid_friendly = 0
    prepackaged = 0

    for d in dishes:
        type_counts[d.dish_type.value] = type_counts.get(d.dish_type.value, 0) + 1
        diff_counts[d.difficulty.value] = diff_counts.get(d.difficulty.value, 0) + 1
        price_counts[d.price_level.value] = price_counts.get(d.price_level.value, 0) + 1
        spicy_counts[d.spicy_level.value] = spicy_counts.get(d.spicy_level.value, 0) + 1
        if d.variant_group:
            variant_groups.add(d.variant_group)
        if d.is_seasonal:
            seasonal += 1
        if d.kid_friendly:
            kid_friendly += 1
        if d.has_prepackaged:
            prepackaged += 1

    print(f"  大荤/小荤/全素:  {type_counts.get('大荤', 0)}/{type_counts.get('小荤', 0)}/{type_counts.get('全素', 0)}")
    print(f"  简单/中等/困难:  {diff_counts.get('简单', 0)}/{diff_counts.get('中等', 0)}/{diff_counts.get('困难', 0)}")
    print(f"  便宜/中等/较贵:  {price_counts.get('便宜', 0)}/{price_counts.get('中等', 0)}/{price_counts.get('较贵', 0)}")
    print(f"  不辣/可免辣/辣:  {spicy_counts.get('不辣', 0)}/{spicy_counts.get('可免辣', 0)}/{spicy_counts.get('辣', 0)}")
    print(f"  有季节限制:      {seasonal} 道")
    print(f"  儿童友好:        {kid_friendly} 道")
    print(f"  有预制菜:        {prepackaged} 道")
    print(f"  变体组数:        {len(variant_groups)} 个 ({', '.join(variant_groups) if variant_groups else '-'})")
    print(f"{'=' * 40}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="菜品数据命令行管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python cli.py list
  python cli.py show 番茄炒蛋
  python cli.py search 排骨
  python cli.py add
  python cli.py edit 番茄炒蛋
  python cli.py delete 测试菜
  python cli.py stats
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # list
    list_parser = subparsers.add_parser("list", help="列出所有菜品")
    list_parser.add_argument("--group", help="按变体组过滤")

    # show
    show_parser = subparsers.add_parser("show", help="查看单道菜详情")
    show_parser.add_argument("name", help="菜名")

    # search
    search_parser = subparsers.add_parser("search", help="搜索菜品")
    search_parser.add_argument("keyword", help="关键词")

    # add
    subparsers.add_parser("add", help="交互式新增菜品")

    # edit
    edit_parser = subparsers.add_parser("edit", help="编辑菜品")
    edit_parser.add_argument("name", help="菜名")

    # delete
    delete_parser = subparsers.add_parser("delete", help="删除菜品")
    delete_parser.add_argument("name", help="菜名")

    # stats
    subparsers.add_parser("stats", help="数据统计")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "list": cmd_list,
        "show": cmd_show,
        "search": cmd_search,
        "add": cmd_add,
        "edit": cmd_edit,
        "delete": cmd_delete,
        "stats": cmd_stats,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
