from recipes import recipes
import random

# 根据菜单生成购物清单

def get_shopping_list(menu, recipes):
    shopping_list = set()  # 使用集合避免重复食材
    for dish in menu:
        if dish in recipes:
            ingredients = recipes[dish]
            shopping_list.update(ingredients)  # 将食材添加到购物清单中
        else:
            print(f"菜谱中没有找到 {dish} 的食材信息。")
    return shopping_list

# 推荐菜谱函数
def recommend_meals(recipes, history):
    # 步骤1: 获取所有可用的菜名（从菜谱字典的键中提取）
    all_dishes = list(recipes.keys())
    
    # 步骤2: 过滤掉最近三天吃过的菜（确保不推荐重复的菜）
    available_dishes = [dish for dish in all_dishes if dish not in history]
    
    # 步骤3: 从可用菜中随机选择两个菜
    # 如果可用菜少于两个，返回所有可用的；否则随机选两个
    if len(available_dishes) < 2:
        recommended = available_dishes
    else:
        recommended = random.sample(available_dishes, 2)
    
    # 步骤4: 返回推荐的菜列表
    return recommended

menu = ["番茄炒蛋", "青椒肉丝"]

shopping_list = get_shopping_list(menu, recipes)

print(shopping_list)

# 示例使用推荐函数
history = ["番茄炒蛋", "青椒肉丝"]  # 假设最近三天吃过这两个
recommended = recommend_meals(recipes, history)
print("推荐的菜:", recommended)

