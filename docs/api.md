# HTTP API 契约

服务提供兼容 OCS AnswererWrapper 的 HTTP 接口。

## 健康检查

`GET /` 或 `HEAD /`

```json
{"status":"ok"}
```

## 查询答案

### GET `/query`

| 参数 | 必需 | 格式 |
|------|------|------|
| `title` | 是 | 非空题目文本 |
| `type` | 是 | 题型标识 |
| `options` | 否 | JSON 数组字符串；不是有效 JSON 时，按换行拆分为选项文本 |

示例：

```bash
curl --get 'http://localhost:8000/query' \
  --data-urlencode 'title=地理学的对象是什么？' \
  --data-urlencode 'type=single' \
  --data-urlencode 'options=["地理环境","地理法则"]'
```

### POST `/query`

请求体为 JSON：

```json
{
  "title": "地理学的对象是什么？",
  "type": "single",
  "options": ["地理环境", "地理法则"]
}
```

选项支持字符串数组，也支持带显式标签的对象数组：

```json
{
  "title": "选择答案",
  "type": "single",
  "options": [
    {"label": "B", "text": "选项二"},
    {"label": "D", "text": "选项四"}
  ]
}
```

对象的 `text` 必须是非空字符串；`label` 可省略，提供时必须是单个英文字母。同一请求中标签（包括省略后按位置生成的 A、B、C……）不可重复。最多 26 个选项。

## 题型与答案

| 题型 | `type` 值 | 成功响应中的 `answer` |
|------|-----------|------------------------|
| 单选题 | `single` | 一个选项标签，如 `"B"` |
| 多选题 | `multiple` | `#` 分隔的标签，如 `"A#C"` |
| 判断题 | `judge`、`judgement`、`judgment`、`truefalse`、`tf` | `"正确"` 或 `"错误"` |

题型标识不区分大小写。当前不支持填空题、简答题或其他题型。

## 响应

成功时 HTTP 响应体：

```json
{
  "code": 0,
  "data": {
    "answer": "B",
    "question": "地理学的对象是什么？",
    "ai": true
  }
}
```

错误时响应体：

```json
{"code":40003,"message":"title too long"}
```

当前主要错误码：

| 错误码 | 含义 |
|--------|------|
| `40001` | 请求体校验失败，或 GET 缺少题目 |
| `40002` | GET 缺少题型，或题型不受支持 |
| `40003` | 题目过长、选项过多、选项标签重复或 GET 选项格式错误 |
| `50001` | 模型配置缺失、配置值无效或模型答案无法解析 |
| `50201` | 模型 API 返回 HTTP 错误或无法连接 |

模型答案无法解析时，服务返回错误而不是生成一个无法确认的答案。错误消息可包含模型解析或配置问题；不得在其中加入 API Key。

## OCS AnswererWrapper

将 `url` 配置为服务的 `/query`，并传入 `title`、`options`、`type`。成功结果从 `res.data` 读取；失败结果从 `res.message` 读取。可参考仓库根目录 [README.md](../README.md) 中的完整配置示例。
