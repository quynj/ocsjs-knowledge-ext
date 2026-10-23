# OCS AnswererWrapper Service (FastAPI)

本服务提供与 OCS AnswererWrapper 兼容的 HTTP 接口，通过用户在`.env`文件中配置兼容OpenAI的接口，实现人工智能自动搜题。

参考：
- 开发文档-AnswererWrapper: https://docs.ocsjs.com/docs/other/api#AnswererWrapper
- 自动答题教程: https://docs.ocsjs.com/docs/work
- ocsjs 仓库: https://github.com/ocsjs/ocsjs

## 使用

- 复制`.env.example`为`.env`，配置`OPEN_AI_API_KEY`、`OPEN_AI_MODEL`以及模型服务的`OPEN_AI_BASE_URL`。
- 默认请求 OpenAI Chat Completions API。如服务兼容 Responses API，将`OPEN_AI_API_TYPE`设为`responses`；默认值为`chat_completions`。
- `OPEN_AI_BASE_URL`填写 API 根地址（通常以`/v1`结尾），使用 OpenAI 官方服务时可以留空。
- 支持单选题（`single`）、多选题（`multiple`）和判断题（`judge`、`judgement`、`judgment`、`truefalse`或`tf`）；其他题型暂不支持。

- 安装`UV`(强大的python包管理工具):

```bash
# 安装 uv
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

多选题的`answer`使用`#`分隔，例如`"A#C"`；判断题的`answer`为`"正确"`或`"错误"`。也支持以 JSON 请求体调用`POST /query`：

```json
{"title":"地理学的对象是什么？","type":"single","options":["地理环境","地理法则"]}
```

失败：

```json
{"code":40001,"message":"missing title"}
```

## 答案准确性说明

>> 部分场景可能需要提高错误率或提高正确率，可参考该说明

本服务使用大语言模型生成答案，答案的准确性无法得到完全保证。模型回答具有一定随机性，`temperature`等参数可以影响回答的随机程度，但不能保证答案正确。

例如，可以在`.env`中设置较高的温度：

```env
OPEN_AI_TEMPERATURE=1.8
```

较高的`temperature`通常会让模型回答更随机，更波动，因此可能对错误率有一点帮助；但它不是正确率错误率调节旋钮，不能保证答案完全正确或完全错误，实际效果也取决于模型和题目。


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
    "handler": "return (res)=>res.code !== 0 ? [res.message, undefined] : [res.data.question,res.data.answer,{ai: res.data.ai}]"
  }
]
```

## 开发文档

开发者和编码 Agent 可从 [docs/README.md](./docs/README.md) 开始，了解项目架构、本地配置、API 契约和新增题型步骤。

## 免责声明

本工具仅供个人学习与技术交流使用。使用者应自行确认使用本工具符合所在课程及平台的相关规定，并对使用本工具产生的内容、操作及后果负责。AI 生成内容可能存在错误，开发者不对其准确性或完整性作出保证。