#!/usr/bin/env python3
"""
推荐引擎主逻辑

三层架构：过滤 → 评分 → 组合
"""

import random
from datetime import datetime
from itertools import product
from typing import Optional

from db import get_all_dishes, get_recent_dishes
from models import Dish, MealConfig, MealPlan, Difficulty, DishType


def _is_summer(month: int) -> bool:
    return month in (6, 7, 8)


def _is_winter(month: int) -> bool:
    return month in (12, 1, 2)


def filter_dishes(dishes: list[Dish], config: MealConfig, month: int) -> list[Dish]:
    """第一层：根据硬约束过滤菜品"""
    result = []
    for dish in dishes:
        # 工作日约束：汤菜单独处理（可提前炖），只过滤主菜
        if config.day_type == "工作日" and not dish.is_soup:
            if dish.total_time > 35 or dish.difficulty == Difficulty.HARD:
                continue

        # 季节约束
        if dish.seasonal_months and month not in dish.seasonal_months:
            continue

        result.append(dish)

    return result


def score_dish(dish: Dish, config: MealConfig, month: int, recent_dishes: list[str]) -> int:
    """第二层：给单道菜打分"""
    score = 50  # 基础分

    # 季节强推
    if dish.seasonal_months and month in dish.seasonal_months:
        score += 30

    # 季节弱推
    if _is_summer(month) and dish.summer_recommended:
        score += 15
    if _is_winter(month) and dish.winter_recommended:
        score += 15

    # 家人爱吃
    for person in config.liked_by if hasattr(config, 'liked_by') else []:
        if person in dish.liked_by:
            score += 20
    # 如果没有 liked_by 配置，默认给有 liked_by 的菜加一点分
    if not (hasattr(config, 'liked_by') and config.liked_by):
        if dish.liked_by:
            score += 10

    # 近期没做
    if dish.name not in recent_dishes:
        score += 50

    # 快菜加分（工作日）
    if config.day_type == "工作日" and dish.total_time <= 20:
        score += 15

    # 预制菜备选
    if dish.has_prepackaged:
        score += 5

    return score


def _get_variant_group_last_used(variants_history: dict[str, str]) -> dict[str, str]:
    """获取每个变体组最近做的菜"""
    return variants_history


def _filter_by_variant_group(dishes: list[Dish], selected: list[Dish]) -> list[Dish]:
    """过滤掉与已选菜同变体组的菜"""
    used_groups = {d.variant_group for d in selected if d.variant_group}
    return [d for d in dishes if not d.variant_group or d.variant_group not in used_groups]


def _has_kid_friendly(dishes: list[Dish]) -> bool:
    """检查是否至少有一道儿童友好且不辣的菜"""
    return any(d.kid_friendly and d.spicy_level.value == "不辣" for d in dishes)


def generate_meal_plan(dishes: list[Dish], config: MealConfig, month: int, all_dishes: list[Dish]) -> Optional[MealPlan]:
    """第三层：组合优化，生成最优菜单"""
    recent = get_recent_dishes(days=7)

    # 给所有菜打分
    scored = [(d, score_dish(d, config, month, recent)) for d in dishes]
    scored.sort(key=lambda x: x[1], reverse=True)

    # 按类型分组，取每组前 N 个作为候选
    pools = {
        DishType.BIG_MEAT: [],
        DishType.SMALL_MEAT: [],
        DishType.VEGETARIAN: [],
        "soup": [],
    }
    for dish, score in scored:
        if dish.is_soup:
            pools["soup"].append((dish, score))
        elif dish.dish_type == DishType.BIG_MEAT:
            pools[DishType.BIG_MEAT].append((dish, score))
        elif dish.dish_type == DishType.SMALL_MEAT:
            pools[DishType.SMALL_MEAT].append((dish, score))
        elif dish.dish_type == DishType.VEGETARIAN:
            pools[DishType.VEGETARIAN].append((dish, score))

    # 配餐数量
    main_count = config.suggested_main_dishes
    need_soup = config.need_soup

    # 从各池取候选（每池最多取前 5 个，控制组合数）
    candidates = {
        DishType.BIG_MEAT: [d for d, _ in pools[DishType.BIG_MEAT][:5]],
        DishType.SMALL_MEAT: [d for d, _ in pools[DishType.SMALL_MEAT][:5]],
        DishType.VEGETARIAN: [d for d, _ in pools[DishType.VEGETARIAN][:5]],
        "soup": [d for d, _ in pools["soup"][:5]],
    }

    # 构建主菜候选池（大荤 + 小荤 + 全素合并，但保留类型信息）
    main_candidates = []
    main_candidates.extend([(d, DishType.BIG_MEAT) for d in candidates[DishType.BIG_MEAT]])
    main_candidates.extend([(d, DishType.SMALL_MEAT) for d in candidates[DishType.SMALL_MEAT]])
    main_candidates.extend([(d, DishType.VEGETARIAN) for d in candidates[DishType.VEGETARIAN]])

    if len(main_candidates) < main_count:
        return None

    # 穷举主菜组合
    best_plan = None
    best_score = -1

    # 从主菜候选中选 main_count 道
    from itertools import combinations
    for combo in combinations(main_candidates, main_count):
        selected_dishes = [d for d, _ in combo]
        types = [t for _, t in combo]

        # 约束检查
        # 1. 不重复变体组
        groups = [d.variant_group for d in selected_dishes if d.variant_group]
        if len(groups) != len(set(groups)):
            continue

        # 2. 荤素搭配（2人以上）
        if config.people_count >= 2:
            has_meat = any(t in (DishType.BIG_MEAT, DishType.SMALL_MEAT) for t in types)
            has_veg = DishType.VEGETARIAN in types
            if not (has_meat and has_veg):
                continue

        # 3. 儿童友好（简化：假设有儿童在场时检查）
        if config.people_count >= 2 and not _has_kid_friendly(selected_dishes):
            continue

        # 计算主菜分数
        main_score = sum(score_dish(d, config, month, recent) for d in selected_dishes)

        # 如果需要汤
        total_dishes = selected_dishes.copy()
        if need_soup:
            soup_candidates = candidates["soup"]
            # 过滤掉与主菜同变体组的汤
            soup_candidates = _filter_by_variant_group(soup_candidates, selected_dishes)
            # 如果季节过滤后没有汤，从所有汤里补（忽略季节）
            if not soup_candidates:
                all_soups = [d for d in all_dishes if d.is_soup]
                all_soups = _filter_by_variant_group(all_soups, selected_dishes)
                if all_soups:
                    soup_candidates = all_soups
                else:
                    continue
            best_soup = max(soup_candidates, key=lambda d: score_dish(d, config, month, recent))
            total_dishes.append(best_soup)
            main_score += score_dish(best_soup, config, month, recent)

        if main_score > best_score:
            best_score = main_score
            best_plan = MealPlan(dishes=total_dishes)

    return best_plan


def recommend(config: MealConfig, month: Optional[int] = None) -> Optional[MealPlan]:
    """
    主推荐入口

    参数:
        config: 用餐配置
        month: 当前月份（1-12），默认取系统当前月份

    返回:
        MealPlan 或 None（无合法组合）
    """
    if month is None:
        month = datetime.now().month

    all_dishes = get_all_dishes()
    if not all_dishes:
        return None

    filtered = filter_dishes(all_dishes, config, month)
    if not filtered:
        return None

    return generate_meal_plan(filtered, config, month, all_dishes)


if __name__ == "__main__":
    # 简单自测
    from db import init_db
    from import_data import rebuild_db

    init_db()
    rebuild_db()

    config = MealConfig(people_count=3, day_type="工作日", need_soup=True)
    plan = recommend(config, month=5)

    if plan:
        print("🍽️  推荐菜单:")
        for i, d in enumerate(plan.dishes, 1):
            tag = "汤" if d.is_soup else d.dish_type.value
            print(f"  {i}. {d.name} ({tag}, {d.total_time}分钟)")
        print(f"\n⏱️  预估总耗时: {plan.total_time} 分钟")
        print(f"🛒 购物清单: {plan.shopping_list}")
    else:
        print("无法生成推荐菜单")
