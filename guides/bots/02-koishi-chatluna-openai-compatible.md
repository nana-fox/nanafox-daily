---
title: "Koishi 的 ChatLuna 怎么配置 OpenAI 兼容接口"
slug: "koishi-chatluna-openai-compatible"
description: "在 Koishi 中为 ChatLuna v1 安装 OpenAI Like 或 OpenAI 适配器，配置 API 地址并用模型指令测试。"
keywords:
  - Koishi OpenAI 兼容
  - ChatLuna OpenAI Like
  - ChatLuna API 请求地址
date: "2026-11-26"
category: "bot-integration"
---

# Koishi 的 ChatLuna 怎么配置 OpenAI 兼容接口

## 适用场景

你在 Koishi 中运行 ChatLuna v1，想给聊天接上支持 OpenAI Chat Completions 的模型服务。ChatLuna v1 提供 OpenAI 和 OpenAI Like 两个适配器。接 OpenAI 官方接口可用 OpenAI 适配器，自建网关或第三方兼容服务可用 OpenAI Like，便于为不同端点单独命名。ChatLuna v2 的配置入口以你的版本为准。[ChatLuna v1 模型平台](https://v1.chatluna.chat/guide/configure-model-platform/introduction.html) · [ChatLuna v2 模型与提供商](https://chatluna.chat/manual/usage/models.html)

## 在 Koishi 配置 ChatLuna v1

1. 在 Koishi 控制台装好并启用 ChatLuna 主插件，再到插件市场搜索 `chatluna-openai-like-adapter`。启用适配器之前，先打开它的配置页。[ChatLuna v1 快速上手](https://v1.chatluna.chat/guide/getting-started.html) · [OpenAI Like 适配器文档](https://v1.chatluna.chat/guide/configure-model-platform/openai-like.html)
2. 给 `platform` 填一个未被占用的平台名。在「请求设置」的 `apiKeys` 中填写同一行的「API Key」「API 请求地址」，并开启该行。请求地址填到服务商给出的 API 基础路径。使用 Chat Completions 时，若适配器提供 `responseApi` 开关，请保持关闭。[OpenAI Like 配置字段](https://github.com/ChatLunaLab/chatluna/blob/2702fe4c0160ef0609fc802345ceb7869091703b/packages/adapter-openai-like/src/index.ts) · [中文字段说明](https://github.com/ChatLunaLab/chatluna/blob/2702fe4c0160ef0609fc802345ceb7869091703b/packages/adapter-openai-like/src/locales/zh-CN.schema.yml)
3. 保存并运行适配器，到沙盒或已接入的聊天平台执行 `chatluna.model.list` 查看模型。用 `chatluna.model.test 平台名/模型ID` 测指定模型，再用 `chatluna.use.model 平台名/模型ID` 切换当前会话并发一条短消息。[ChatLuna v1 模型指令](https://v1.chatluna.chat/guide/useful-commands/model.html)
4. 如果改用 `chatluna-openai-adapter`，在其配置页的 `apiKeys` 行填写 API Key。自定义端点时，再填「OpenAI API 的请求地址」，保存并运行后用 `openai/模型ID` 测试。[OpenAI 适配器文档](https://v1.chatluna.chat/guide/configure-model-platform/openai.html) · [OpenAI 适配器中文字段说明](https://github.com/ChatLunaLab/chatluna/blob/2702fe4c0160ef0609fc802345ceb7869091703b/packages/adapter-openai/src/locales/zh-CN.schema.yml)

## 以 NanaFox Router 为例

在接入引导中选「Cherry Studio / Cursor 等客户端」，使用「OpenAI GPT」分组的 API Key。[打开 Router 客户端接入入口](https://router.nanafox.com/register?aff=UG937JQ67MRS&use=client&utm_source=nanafox_daily&utm_medium=site)

- 在 OpenAI Like 适配器中，把 `platform` 设为 `nanafox-router`。如果这个名字已占用，换一个，并在下面的命令里使用新名字。
- 在 `apiKeys` 同一行填 Router 密钥和 `https://router.nanafox.com/v1`，保存并启用。
- 测试 `gpt-6.1-sol`。如果 Router 的模型列表有变动，使用当前密钥可用的模型 ID。

```text
chatluna.model.test nanafox-router/gpt-6.1-sol
chatluna.use.model nanafox-router/gpt-6.1-sol
```

## 常见报错

- **401 Unauthorized**　检查失败请求所属的平台和 `apiKeys` 中启用的那一行，确认该行的密钥与请求地址匹配。
- **404 Not Found**　日志里的 `/models` 和 `/chat/completions` 是两条请求。先确认哪条失败，再检查 Router 请求是否分别到 `/v1/models` 和 `/v1/chat/completions`。用同一密钥查不到模型列表时，且服务商确认支持对话接口，可以在 OpenAI Like 的 `additionalModels` 填入服务商给出的模型 ID，再关闭 `pullModels` 试一次。字段以你的版本为准。[OpenAI Like 模型配置源码](https://github.com/ChatLunaLab/chatluna/blob/2702fe4c0160ef0609fc802345ceb7869091703b/packages/adapter-openai-like/src/client.ts)
- **模型不存在**　查 `chatluna.model.list` 中的完整名称。平台名前缀写在 ChatLuna 的选择和测试命令里，适配器的额外模型条目里填服务商原始 ID。核对密钥是否有权访问该模型。
- **请求超时**　从 Koishi 实际运行的主机或容器检查网络和代理设置，先对单个模型运行 `chatluna.model.test`。如果模型测试能回复，回到新会话试一条短文本，再比较两次日志。
