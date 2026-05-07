from recipes import recipes

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

menu = ["番茄炒蛋", "青椒肉丝"]

shopping_list = get_shopping_list(menu, recipes)

print(shopping_list)

