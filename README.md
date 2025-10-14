# OCS AnswererWrapper Service (FastAPI)

本服务提供与 OCS AnswererWrapper 兼容的 HTTP 接口，通过用户在`.env`文件中配置兼容OpenAI的接口，实现人工智能自动搜题。

参考：
- 开发文档-AnswererWrapper: https://docs.ocsjs.com/docs/other/api#AnswererWrapper
- 自动答题教程: https://docs.ocsjs.com/docs/work
- ocsjs 仓库: https://github.com/ocsjs/ocsjs

## 使用

- 先将`.env.example`文件重命名为`.env`,然后配置`OPEN_AI_API_KEY`、`OPEN_AI_BASE_URL`、`OPEN_AI_MODEL`

- 安装`UV`(强大的python包管理工具):

```bash
# 安装 uv（如未安装,下载慢自己上网解决）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 同步依赖
uv sync

# 运行服务
uv run fastapi dev
```

## GET 示例

```bash
curl "http://localhost:8000/query?title=%E5%9C%B0%E7%90%86%E5%AD%A6%E7%9A%84%E5%AF%B9%E8%B1%A1%E6%98%AF%E4%BB%80%E4%B9%88%EF%BC%9F&type=single&options=%5B%22%E5%9C%B0%E7%90%86%E7%8E%AF%E5%A2%83%22,%22%E5%9C%B0%E7%90%86%E6%B3%95%E5%88%99%22%5D"
```

成功：

```json
{"code":0,"data":{"answer":"A","question":"...","ai":true}}
```

失败：

```json
{"code":40001,"message":"missing title"}
```

## OCS AnswererWrapper 配置

```json
[
  {
    "name": "ocsjs-knowledge-ext",
    "homepage": "http://localhost:8000/",
    "url": "http://localhost:8000/query",
    "method": "get",
    "type": "GM_xmlhttpRequest",
    "contentType": "json",
    "data": {
        "title": "${title}",
        "options": "${options}",
        "type": "${type}"
    },
    "handler": "return (res)=>res.code !== 0 ? [res.data.answer, undefined] : [res.data.question,res.data.answer,{ai: res.data.ai}]"
  }
]
```

## 拓展ollma
- 可以让AI帮你实现ollma版本，调用本地的api，无需依赖第三方api服务
- ocsjs脚本最大搜题限制60秒，需考虑本地模型响应速度
- 无需让本地模型具备联网搜索功能，依靠llm自身预训练数据即可

## 免责声明
- 本脚本仅供参考学习使用，使用之后导致的账号被封禁等违规情况与本人无关