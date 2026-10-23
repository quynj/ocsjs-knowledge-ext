# 开发文档

这组文档帮助开发者和编码 Agent 快速理解、运行和扩展 OCS AnswererWrapper 服务。

## 推荐阅读顺序

1. [架构与请求流程](./architecture.md)：了解模块职责和从 HTTP 请求到模型答案的调用路径。
2. [配置与开发](./development.md)：本地启动、环境变量、测试和代码约定。
3. [API 契约](./api.md)：查看 GET/POST 参数、选项格式和返回结构。
4. [扩展题型](./question-types.md)：按步骤添加题型并了解需要覆盖的测试。

## 项目范围

- 服务将 OCS 题目请求转发给配置的 OpenAI 兼容模型。
- 当前支持单选题 `single`、多选题 `multiple` 和判断题 `judge`、`judgement`、`judgment`、`truefalse`、`tf`。
- 模型请求支持 Chat Completions 与 Responses API，通过环境变量选择。
- 题库当前不包含本地持久化题目或检索索引；答案来自已配置的模型。
- 其他题型尚未实现。新增题型时应同步更新校验、提示词、答案解析、文档和测试。

## Agent 开发约定

- 先阅读相关模块和测试，再作最小范围修改；不要假设未实现的题型行为。
- 保持 OCS 成功响应结构与答案编码兼容；接口变更必须更新 [API 契约](./api.md)。
- 模型返回内容必须经过题型解析和校验；不确定或无法解析时返回错误，不能伪造成功答案。
- 不记录 API Key、Authorization Header 或其他凭据；测试一律使用虚构凭据和 mock。
- 增加或修改运行依赖时，同时检查 `pyproject.toml` 与 `uv.lock`。
- 完成后运行 `uv run python -m unittest discover -s tests -v` 和 `git diff --check`。
