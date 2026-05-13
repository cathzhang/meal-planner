# Meal Planner — Agent 工作指南

## 项目概况

**家庭菜单推荐系统**。根据家庭成员、季节、时间、预算等约束，智能推荐"今天吃什么"，并生成购物清单。

- **技术栈**：Python + SQLite
- **Python 环境**：`/opt/anaconda3/bin/python`（3.12.9），所有依赖和运行都使用该路径
- **主要文件**：`cli.py`（交互入口）、`models.py`（数据模型）、`db.py`（数据库）、`add_recipe.py`（录入工具）
- **数据文件**：`data/recipes.json`（菜品数据源）、`meal_planner.db`（SQLite 数据库）

---

## 写文档规范

### 输出位置与命名
- 需求/设计文档放在项目根目录
- 给飞书的知识库文档命名为 `docs_for_feishu.md`
- 其他技术文档以 `.md` 后缀放在项目根目录或 `docs/` 子目录

### 文档格式
- 使用 Markdown
- 标题层级：`#` 项目/文档名 → `##` 章节 → `###` 小节
- 表格用标准 Markdown 表格语法
- 代码块标注语言类型

### 关键文档
- `REQUIREMENTS.md`：项目需求总览，包含菜品数据结构、用餐场景配置等

---

## 飞书文档上传

**环境已配置，可直接使用。**

```bash
# 已安装的包
feishu-docx==0.2.5    # 飞书文档读写工具
lark-oapi==1.6.2      # 飞书开放平台 SDK

# 配置文件
~/.feishu-docx/config.json
```

**目标知识库：**

| 知识库名称 | space_id |
|-----------|----------|
| 今天吃什么 | `7627372929830898628` |

### 上传方式

**方式一：使用已有脚本（推荐）**

项目根目录已有 `publish_to_feishu.py`，可直接运行：

```bash
cd /Users/cathy/Documents/workspace/meal-planner
python3 publish_to_feishu.py
```

> 该脚本默认上传 `docs_for_feishu.md` 到"今天吃什么"知识库，标题为"项目需求文档"。

**方式二：自定义上传**

如需上传其他 Markdown 文件或修改标题，可直接调用 `feishu_docx` 或 `lark_oapi`：

```python
from feishu_docx.core.writer import FeishuWriter

writer = FeishuWriter()
doc = writer.create_document(title="文档标题", content="# Markdown内容")
```

或参考 `publish_to_feishu.py` 中的 `lark_oapi` 调用方式，直接操作 API。

### 注意事项
- 上传前确保飞书应用已被添加到"今天吃什么"知识库的协作者中
- `MarkdownToBlocks` 转换时会过滤表格等复杂嵌套块，如需完整表格支持，需手动调整 block 结构
- 文档创建后可在飞书 wiki 中调整目录位置

---

## 用户偏好

- **输出语言**：中文
- **菜品数据**：以 `data/recipes.json` 为数据源，SQLite 为运行时存储
- **代码风格**：简洁实用，优先用 Python 标准库，减少外部依赖
