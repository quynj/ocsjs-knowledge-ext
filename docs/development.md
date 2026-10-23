# 配置与本地开发

## 环境要求

- Python 3.11 或更高版本
- [uv](https://docs.astral.sh/uv/)
- 一个兼容 OpenAI API 的模型服务及对应 API Key

## 首次启动

在仓库根目录执行：

```bash
cp .env.example .env
# 编辑 .env，设置 OPEN_AI_API_KEY 和 OPEN_AI_MODEL
uv sync
uv run fastapi dev
```

开发服务器启动后可访问 `http://localhost:8000/` 查看健康状态，或访问 `http://localhost:8000/docs` 查看 FastAPI 生成的交互式接口文档。

## 环境变量

| 变量 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `OPEN_AI_API_KEY` | 是 | 空 | 模型服务 API Key |
| `OPEN_AI_MODEL` | 是 | 空 | 服务端使用的模型名称 |
| `OPEN_AI_BASE_URL` | 否 | `https://api.deepseek.com` | API 根 URL，通常包含 `/v1`；代码会去除末尾斜杠 |
| `OPEN_AI_API_TYPE` | 否 | `chat_completions` | `chat_completions` 或 `responses` |

`OPEN_AI_API_TYPE` 决定调用的端点与请求格式。请确认所选模型服务实际支持对应端点。超时时间当前固定为 60 秒，最长题目为 2000 字符，选项上限为 26。

## 验证

运行完整测试：

```bash
uv run python -m unittest discover -s tests -v
```

运行 Python 语法编译和差异空白检查：

```bash
uv run python -m compileall -q app tests
git diff --check
```

测试应通过 mock 模型调用，不访问真实模型服务，也不需要有效 API Key。

## 常见开发任务

- 修改接口字段或响应：阅读 [API 契约](./api.md)，并更新端点测试和 README 示例。
- 添加题型：按 [扩展题型](./question-types.md) 同步实现所有题型表面。
- 修改模型供应商协议：只在 `llm.py` 增加/调整协议适配，并覆盖请求与响应测试；不要将凭据放入仓库。
- 新增依赖：修改 `pyproject.toml` 后运行 `uv lock`，提交更新后的 `uv.lock`。

## 日志与凭据

不要提交 `.env`，不要把 API Key 放进 URL、日志、示例响应、测试代码或文档。测试凭据必须为不可用的虚构值。
