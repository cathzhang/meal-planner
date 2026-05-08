from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class DishType(str, Enum):
    """菜品类型"""
    BIG_MEAT = "大荤"      # 纯肉菜，如红烧排骨
    SMALL_MEAT = "小荤"    # 有肉有素，如青椒肉丝
    VEGETARIAN = "全素"    # 纯素菜，如番茄炒蛋


class Difficulty(str, Enum):
    """制作难易程度"""
    EASY = "简单"          # 10分钟内，步骤少
    MEDIUM = "中等"        # 10-30分钟，步骤适中
    HARD = "困难"          # 30分钟以上，或技巧要求高


class SpicyLevel(str, Enum):
    """辣味等级"""
    NONE = "不辣"
    REMOVABLE = "可免辣"    # 默认辣，但可以去掉
    SPICY = "辣"            # 必须辣，去辣没灵魂


class PriceLevel(str, Enum):
    """菜价评估（按主食材估算）"""
    CHEAP = "便宜"          # 人均 < 5元，如番茄炒蛋
    MEDIUM = "中等"         # 人均 5-15元，如青椒肉丝
    EXPENSIVE = "较贵"      # 人均 > 15元，如红烧排骨


@dataclass
class Dish:
    """
    菜品数据模型
    
    设计说明：
    - 食材 ingredients: 只记录主要食材，普通油盐糖等基础调料不列入
    - 酱料 sauces: 单独记录特殊酱料，方便采购和备货
    - cook_time_minutes: 灶上实际制作时间
    - prep_time_minutes: 备菜时间（切配、腌制等）
    - 难度 difficulty: 简单/中等/困难
    - 类型 dish_type: 大荤/小荤/全素，用于荤素搭配推荐
    - 季节推荐: 布尔值标记，可同时属于多个季节
    - 喜好人员 liked_by: 家庭成员名单，空列表表示无人特别偏好
    - 辣味 spicy_level: 不辣/可免辣/辣
    - 儿童友好: 口味温和、食材安全、不刺激
    - 季节性 seasonal_months: 空列表表示全年都有，否则填月份[1-12]
    - 菜价 price_level: 便宜/中等/较贵，用于预算控制
    - 预制菜 has_prepackaged: 是否有成熟预制菜可选
    """
    name: str                      # 菜名
    ingredients: List[str]         # 主要食材（不含油盐等基础调料）
    sauces: List[str]              # 特殊酱料/调味料（如豆瓣酱、蚝油等）
    cook_time_minutes: int         # 灶上制作时间（分钟）
    prep_time_minutes: int         # 备菜时间（分钟）：切丝、腌制等
    difficulty: Difficulty         # 难易程度
    dish_type: DishType            # 菜品类型
    summer_recommended: bool       # 夏日推荐
    winter_recommended: bool       # 冬日推荐
    liked_by: List[str] = field(default_factory=list)  # 谁喜欢这道菜
    spicy_level: SpicyLevel = SpicyLevel.NONE           # 辣味等级
    kid_friendly: bool = False     # 是否适合儿童食用
    seasonal_months: List[int] = field(default_factory=list)  # 适合月份[1-12]，空=全年
    price_level: PriceLevel = PriceLevel.MEDIUM         # 菜价评估
    has_prepackaged: bool = False  # 是否有成熟预制菜
    variant_group: Optional[str] = None  # 变体组，同组菜可互相替换（如"排骨汤系列"）

    @property
    def total_time(self) -> int:
        """总耗时 = 备菜 + 制作（假设不能并行）"""
        return self.prep_time_minutes + self.cook_time_minutes

    @property
    def is_seasonal(self) -> bool:
        """是否有季节性限制"""
        return len(self.seasonal_months) > 0

    def is_available_in_month(self, month: int) -> bool:
        """判断某个月份是否适合吃这道菜"""
        if not self.seasonal_months:
            return True
        return month in self.seasonal_months


@dataclass
class MealPlan:
    """
    一餐的菜单组合
    
    例如午餐/晚餐的完整搭配
    """
    dishes: List[Dish]             # 这一餐包含的菜品
    meal_time: str = "晚餐"         # 早餐/午餐/晚餐

    @property
    def total_time(self) -> int:
        """估算总制作时间（取最长时间，假设并行制作）"""
        if not self.dishes:
            return 0
        # 备菜可以串行或并行，这里保守取备菜总时间 + 最长制作时间
        total_prep = sum(dish.prep_time_minutes for dish in self.dishes)
        max_cook = max(dish.cook_time_minutes for dish in self.dishes)
        return total_prep + max_cook

    @property
    def shopping_list(self) -> List[str]:
        """生成这一餐的购物清单"""
        ingredients = set()
        sauces = set()
        for dish in self.dishes:
            ingredients.update(dish.ingredients)
            sauces.update(dish.sauces)
        return sorted(list(ingredients) + list(sauces))


# ========== 示例数据 ==========

DISH_DATABASE = [

    Dish(
        name="青椒肉丝",
        ingredients=["青椒", "猪肉"],
        sauces=["生抽", "料酒", "淀粉"],
        cook_time_minutes=20,
        prep_time_minutes=15,
        difficulty=Difficulty.MEDIUM,
        dish_type=DishType.SMALL_MEAT,
        summer_recommended=True,
        winter_recommended=True,
        liked_by=["爸爸"],
        spicy_level=SpicyLevel.REMOVABLE,
        kid_friendly=True,
        seasonal_months=[],
        price_level=PriceLevel.MEDIUM,
        has_prepackaged=False
    ),
    Dish(
        name="麻婆豆腐",
        ingredients=["豆腐", "牛肉末"],
        sauces=["豆瓣酱", "花椒粉", "辣椒油"],
        cook_time_minutes=25,
        prep_time_minutes=10,
        difficulty=Difficulty.MEDIUM,
        dish_type=DishType.BIG_MEAT,
        summer_recommended=False,
        winter_recommended=True,
        liked_by=["爸爸", "妈妈"],
        spicy_level=SpicyLevel.SPICY,
        kid_friendly=False,
        seasonal_months=[],
        price_level=PriceLevel.CHEAP,
        has_prepackaged=True
    ),
    Dish(
        name="鱼香肉丝",
        ingredients=["猪肉", "木耳", "胡萝卜", "青椒"],
        sauces=["豆瓣酱", "醋", "糖", "生抽"],
        cook_time_minutes=30,
        prep_time_minutes=20,
        difficulty=Difficulty.HARD,
        dish_type=DishType.SMALL_MEAT,
        summer_recommended=False,
        winter_recommended=True,
        liked_by=[],
        spicy_level=SpicyLevel.SPICY,
        kid_friendly=False,
        seasonal_months=[],
        price_level=PriceLevel.MEDIUM,
        has_prepackaged=True
    ),
    Dish(
        name="红烧排骨",
        ingredients=["排骨"],
        sauces=["生抽", "老抽", "冰糖", "八角", "桂皮"],
        cook_time_minutes=60,
        prep_time_minutes=15,
        difficulty=Difficulty.HARD,
        dish_type=DishType.BIG_MEAT,
        summer_recommended=False,
        winter_recommended=True,
        liked_by=["全家"],
        spicy_level=SpicyLevel.NONE,
        kid_friendly=True,
        seasonal_months=[],
        price_level=PriceLevel.EXPENSIVE,
        has_prepackaged=False
    ),
    Dish(
        name="蒜蓉西兰花",
        ingredients=["西兰花", "大蒜"],
        sauces=["蚝油"],
        cook_time_minutes=8,
        prep_time_minutes=5,
        difficulty=Difficulty.EASY,
        dish_type=DishType.VEGETARIAN,
        summer_recommended=True,
        winter_recommended=False,
        liked_by=["妈妈"],
        spicy_level=SpicyLevel.NONE,
        kid_friendly=True,
        seasonal_months=[],
        price_level=PriceLevel.CHEAP,
        has_prepackaged=False
    ),
    Dish(
        name="凉拌黄瓜",
        ingredients=["黄瓜", "大蒜", "花生米"],
        sauces=["醋", "辣椒油", "香油"],
        cook_time_minutes=5,
        prep_time_minutes=5,
        difficulty=Difficulty.EASY,
        dish_type=DishType.VEGETARIAN,
        summer_recommended=True,
        winter_recommended=False,
        liked_by=["爸爸", "孩子"],
        spicy_level=SpicyLevel.REMOVABLE,
        kid_friendly=True,
        seasonal_months=[5, 6, 7, 8, 9],
        price_level=PriceLevel.CHEAP,
        has_prepackaged=False
    ),
    Dish(
        name="萝卜炖羊肉",
        ingredients=["羊肉", "白萝卜"],
        sauces=["料酒", "八角", "白芷"],
        cook_time_minutes=90,
        prep_time_minutes=20,
        difficulty=Difficulty.MEDIUM,
        dish_type=DishType.BIG_MEAT,
        summer_recommended=False,
        winter_recommended=True,
        liked_by=["爸爸"],
        spicy_level=SpicyLevel.NONE,
        kid_friendly=True,
        seasonal_months=[11, 12, 1, 2],
        price_level=PriceLevel.EXPENSIVE,
        has_prepackaged=False,
        variant_group="羊肉汤系列"
    ),
    # --- 排骨汤变体系列 ---
    Dish(
        name="冬瓜排骨汤",
        ingredients=["排骨", "冬瓜"],
        sauces=["料酒", "姜片"],
        cook_time_minutes=60,
        prep_time_minutes=15,
        difficulty=Difficulty.EASY,
        dish_type=DishType.BIG_MEAT,
        summer_recommended=True,
        winter_recommended=False,
        liked_by=["妈妈", "孩子"],
        spicy_level=SpicyLevel.NONE,
        kid_friendly=True,
        seasonal_months=[6, 7, 8],
        price_level=PriceLevel.MEDIUM,
        has_prepackaged=False,
        variant_group="排骨汤系列"
    ),
    Dish(
        name="玉米排骨汤",
        ingredients=["排骨", "玉米", "胡萝卜"],
        sauces=["料酒", "姜片"],
        cook_time_minutes=60,
        prep_time_minutes=15,
        difficulty=Difficulty.EASY,
        dish_type=DishType.BIG_MEAT,
        summer_recommended=False,
        winter_recommended=True,
        liked_by=["孩子"],
        spicy_level=SpicyLevel.NONE,
        kid_friendly=True,
        seasonal_months=[9, 10, 11],
        price_level=PriceLevel.MEDIUM,
        has_prepackaged=False,
        variant_group="排骨汤系列"
    ),
    Dish(
        name="萝卜排骨汤",
        ingredients=["排骨", "白萝卜"],
        sauces=["料酒", "姜片"],
        cook_time_minutes=60,
        prep_time_minutes=15,
        difficulty=Difficulty.EASY,
        dish_type=DishType.BIG_MEAT,
        summer_recommended=False,
        winter_recommended=True,
        liked_by=["全家"],
        spicy_level=SpicyLevel.NONE,
        kid_friendly=True,
        seasonal_months=[11, 12, 1, 2],
        price_level=PriceLevel.MEDIUM,
        has_prepackaged=False,
        variant_group="排骨汤系列"
    ),
    # --- 番茄炒蛋变体 ---
    Dish(
        name="番茄炒蛋",
        ingredients=["番茄", "鸡蛋"],
        sauces=["番茄酱"],
        cook_time_minutes=10,
        prep_time_minutes=5,
        difficulty=Difficulty.EASY,
        dish_type=DishType.SMALL_MEAT,
        summer_recommended=True,
        winter_recommended=False,
        liked_by=["妈妈", "孩子"],
        spicy_level=SpicyLevel.NONE,
        kid_friendly=True,
        seasonal_months=[],
        price_level=PriceLevel.CHEAP,
        has_prepackaged=False,
        variant_group="番茄炒蛋系列"
    ),
    Dish(
        name="番茄滑蛋",
        ingredients=["番茄", "鸡蛋"],
        sauces=["番茄酱", "淀粉水"],
        cook_time_minutes=10,
        prep_time_minutes=5,
        difficulty=Difficulty.EASY,
        dish_type=DishType.SMALL_MEAT,
        summer_recommended=True,
        winter_recommended=False,
        liked_by=["孩子"],
        spicy_level=SpicyLevel.NONE,
        kid_friendly=True,
        seasonal_months=[],
        price_level=PriceLevel.CHEAP,
        has_prepackaged=False,
        variant_group="番茄炒蛋系列"
    ),
]

# 为了方便按菜名查找，提供一个字典映射
DISH_BY_NAME = {dish.name: dish for dish in DISH_DATABASE}
