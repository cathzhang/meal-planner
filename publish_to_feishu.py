#!/usr/bin/env python3
import json
import requests
import lark_oapi as lark
from lark_oapi.api.auth.v3 import InternalTenantAccessTokenRequest
from lark_oapi.api.auth.v3.model import InternalTenantAccessTokenRequestBodyBuilder
from lark_oapi.api.wiki.v2 import CreateSpaceNodeRequest
from feishu_docx.core.converters.md_to_blocks import MarkdownToBlocks

CONFIG_PATH = "/Users/cathy/.feishu-docx/config.json"
MD_PATH = "/Users/cathy/Documents/workspace/meal-planner/docs_for_feishu.md"
SPACE_ID = "7627372929830898628"


def main():
    with open(CONFIG_PATH) as f:
        config = json.load(f)

    client = lark.Client.builder() \
        .app_id(config['app_id']).app_secret(config['app_secret']) \
        .log_level(lark.LogLevel.ERROR).build()

    body = InternalTenantAccessTokenRequestBodyBuilder() \
        .app_id(config['app_id']).app_secret(config['app_secret']).build()
    req = InternalTenantAccessTokenRequest.builder().request_body(body).build()
    resp = client.auth.v3.tenant_access_token.internal(req)
    token = json.loads(resp.raw.content.decode())['tenant_access_token']

    # 创建文档节点
    node_req = CreateSpaceNodeRequest.builder() \
        .space_id(SPACE_ID) \
        .request_body({"obj_type": "docx", "title": "项目需求文档", "node_type": "origin"}) \
        .build()
    node_resp = client.wiki.v2.space_node.create(node_req, lark.RequestOption.builder().tenant_access_token(token).build())
    node_data = json.loads(node_resp.raw.content.decode())

    if node_data.get('code', 0) != 0:
        raise RuntimeError(f"创建节点失败: {node_data}")

    document_id = node_data['data']['node']['obj_token']
    print(f"✅ 文档创建成功")

    with open(MD_PATH, encoding='utf-8') as f:
        md_text = f.read()

    # Markdown 转飞书 Blocks（过滤掉表格等复杂嵌套块）
    converter = MarkdownToBlocks()
    blocks, _ = converter.convert(md_text)
    blocks = [b for b in blocks if b.get('block_type') not in (31, 32)]  # 过滤 table/table_cell
    for b in blocks:
        b.pop('children', None)  # 移除嵌套 children

    # 直接用 HTTP API 写入
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks/{document_id}/children"

    # 分批写入（每批50个）
    for i in range(0, len(blocks), 50):
        batch = blocks[i:i+50]
        response = requests.post(url, headers=headers, json={"children": batch})
        result = response.json()
        if result.get('code', 0) != 0:
            raise RuntimeError(f"写入失败: {result}")

    print(f"✅ 写入完成，共 {len(blocks)} 个块")
    print(f"📎 https://www.feishu.cn/docx/{document_id}")


if __name__ == "__main__":
    main()
