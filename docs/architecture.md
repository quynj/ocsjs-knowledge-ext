# 架构与请求流程

## 目录结构

```text
app/
  config.py    环境变量、服务限制、模型 API 类型
  models.py    请求、选项、题型及响应的数据模型
  main.py      FastAPI 应用、HTTP 路由、请求校验及错误映射
  prompt.py    题目与选项的模型提示词
  llm.py       Chat Completions / Responses HTTP 调用及响应文本提取
  parsing.py   把模型文本解析为 OCS 需要的答案
tests/
  test_quiz.py 模型调用、答案解析和 HTTP 契约测试
```

## 请求处理流程

1. `GET /query` 解析查询参数；`POST /query` 从 JSON 请求体接收数据。
2. `QueryRequest` 校验题目、题型和选项结构。当前题型为固定集合，不能在仅添加提示词后就视为已支持。
3. `main.py` 执行题目长度、选项数量和选项标签唯一性检查。
4. `prompt.py` 根据题型生成系统提示词，并为选项组织标签和文本。
5. `config.py` 读取模型配置，`llm.py` 调用所选 API 并提取文本结果。
6. `parsing.py` 将输出归一化为字母答案、多选答案或判断答案；验证失败时请求返回错误。
7. `main.py` 将答案包装为 OCS AnswererWrapper 格式。

## 模块边界

- 路由和 HTTP 输入/输出属于 `main.py`；业务数据形状属于 `models.py`。
- 提示词构造不应负责解释模型输出；解析逻辑不应发起网络请求。
- `llm.py` 负责 API 协议和响应文本提取，不应包含题型特定的答案规则。
- 不要在日志、异常消息或测试快照中输出密钥或 Authorization Header。

## 错误处理

错误以 JSON `{ "code": ..., "message": ... }` 返回。用户输入和题型错误应在调用模型前发现；上游 HTTP 失败返回网关错误；模型内容不能解析时不得返回成功格式。修改错误处理时应同步检查 [API 契约](./api.md)及端点测试。
