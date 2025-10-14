# OCS AnswererWrapper Service (FastAPI)

本服务提供与 OCS AnswererWrapper 兼容的 HTTP 接口，内部将题目转发至用户自带的 OpenAI 兼容 LLM。服务端不提供任何默认 LLM，必须在请求中提供 `baseUrl`、`apiKey`、`model`。

参考：
- 开发文档-AnswererWrapper: https://docs.ocsjs.com/docs/other/api#AnswererWrapper
- 自动答题教程: https://docs.ocsjs.com/docs/work
- ocsjs 仓库: https://github.com/ocsjs/ocsjs

## 使用 uv 管理与启动

```bash
# 安装 uv（如未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 同步依赖
uv sync

# 运行服务
uv run fastapi dev
```

## GET 示例

```bash
curl "http://localhost:8000/query?title=%E5%9C%B0%E7%90%86%E5%AD%A6%E7%9A%84%E5%AF%B9%E8%B1%A1%E6%98%AF%E4%BB%80%E4%B9%88%EF%BC%9F&type=single&options=%5B%22%E5%9C%B0%E7%90%86%E7%8E%AF%E5%A2%83%22,%22%E5%9C%B0%E7%90%86%E6%B3%95%E5%88%99%22%5D&baseUrl=https%3A%2F%2Fapi.openai.com&apiKey=sk-xxx&model=gpt-4o-mini"
```

成功：

```json
{"code":0,"data":{"answer":"A","question":"...","ai":true}}
```

失败：

```json
{"code":40001,"message":"missing baseUrl/apiKey/model"}
```

## OCS AnswererWrapper 配置（GET）

```json
[
  {
    "name": "用户自带LLM题库",
    "homepage": "http://localhost:8000/",
    "url": "http://localhost:8000/query",
    "method": "get",
    "type": "GM_xmlhttpRequest",
    "contentType": "json",
    "data": {
      "title": "${title}",
      "options": "${options}",
      "type": "${type}",
      "baseUrl": "${user.baseUrl}",
      "apiKey": "${user.apiKey}",
      "model": "${user.model}"
    },
    "handler": "return (res)=> res.code === 0 ? [res.data.answer, undefined, { ai: res.data.ai }] : [res.message || '未命中', undefined]"
  }
]
```

如需 POST，将 `method` 改为 `post` 并在 OCS 侧以 JSON 发送相同字段即可。