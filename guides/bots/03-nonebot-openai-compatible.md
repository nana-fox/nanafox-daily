---
title: "NoneBot2 AI 聊天插件怎么接 OpenAI 兼容 API"
slug: "nonebot-openai-compatible"
description: "用 ChatGPT Turbo 和白泽两个 NoneBot2 插件演示 API Key、模型 ID 和地址的填法，区分 Base URL 与完整对话端点。"
keywords:
  - NoneBot OpenAI 兼容
  - nonebot-plugin-chatgpt-turbo oneapi_url
  - NoneBot 白泽 AICHAT_API_URL
date: "2026-11-26"
category: "bot-integration"
---

# NoneBot2 AI 聊天插件怎么接 OpenAI 兼容 API

## 适用场景

你已有能收发消息的 NoneBot2 机器人，想给 AI 聊天插件接上 OpenAI 兼容服务。下面用基于 OneBot v11 的 ChatGPT Turbo 和白泽两个社区插件说明常见的两种填法。先确认正在用的插件包名，同一个服务的地址在两个插件里要填到不同位置。

## 安装并找到配置文件

1. 在 NoneBot2 项目目录和它的 Python 环境中安装所需插件。ChatGPT Turbo 可用 `pip install nonebot-plugin-chatgpt-turbo`。白泽按其 README 的 Git 安装方式操作。用 pip 安装后，确认项目已加载对应模块 `nonebot_plugin_chatgpt_turbo` 或 `nonebot_plugin_aichat_baize`。如果项目在 `pyproject.toml` 中维护插件列表，就把模块名加入现有列表。[NoneBot 安装插件](https://nonebot.dev/docs/tutorial/store) · [ChatGPT Turbo README](https://github.com/Alpaca4610/nonebot_plugin_chatgpt_turbo/blob/d33f5319330eed7a7bd8459add10ef066867ad82/README.md) · [白泽 README](https://github.com/sangonomiya249/nonebot_plugin_aichat_baize/blob/905c041ec5fea114848af62487219be75fc2ea07/README.md)
2. 用 ChatGPT Turbo 时，在项目根目录的 `.env` 写入 `oneapi_key`、`oneapi_url` 和 `oneapi_model`。`oneapi_url` 传给 OpenAI SDK 的 `base_url`，这里只填基础地址。如果改过运行环境，核对 `.env.prod` 或对应的 `.env.<环境名>` 是否覆盖了这些值。[NoneBot 配置加载顺序](https://nonebot.dev/docs/appendices/config) · [ChatGPT Turbo 请求源码](https://github.com/Alpaca4610/nonebot_plugin_chatgpt_turbo/blob/d33f5319330eed7a7bd8459add10ef066867ad82/nonebot_plugin_chatgpt_turbo/__init__.py)
3. 用白泽时，在项目根目录的 `.env` 写入 `AICHAT_API_KEY`、`AICHAT_API_URL` 和 `AICHAT_MODEL_ID`。白泽直接向 `AICHAT_API_URL` 发请求，这里填服务商的完整 Chat Completions 地址。其他插件或不同版本的字段以你的版本为准。[白泽配置源码](https://github.com/sangonomiya249/nonebot_plugin_aichat_baize/blob/905c041ec5fea114848af62487219be75fc2ea07/nonebot_plugin_aichat_baize/config.py) · [白泽请求源码](https://github.com/sangonomiya249/nonebot_plugin_aichat_baize/blob/905c041ec5fea114848af62487219be75fc2ea07/nonebot_plugin_aichat_baize/__init__.py)

## 以 NanaFox Router 为例

在接入引导中选「Cherry Studio / Cursor 等客户端」，使用「OpenAI GPT」分组的密钥。下面只复制当前插件对应的一段，把示例密钥换成自己的密钥。选用其他服务时，同样换成该服务给出的地址、密钥和模型 ID。[打开 Router 客户端接入入口](https://router.nanafox.com/register?aff=UG937JQ67MRS&use=client&utm_source=nanafox_daily&utm_medium=site)

### ChatGPT Turbo

```dotenv
oneapi_url="https://router.nanafox.com/v1"
oneapi_key="sk-your-api-key"
oneapi_model="gpt-6.1-sol"
```

### 白泽

```dotenv
AICHAT_API_URL="https://router.nanafox.com/v1/chat/completions"
AICHAT_API_KEY="sk-your-api-key"
AICHAT_MODEL_ID="gpt-6.1-sol"
```

保存后重启机器人。ChatGPT Turbo 可以用 `chat` 命令发一句短问句，命令前缀以项目配置为准。白泽可以在适用的群里 @ 机器人并发一句短消息。确认日志显示加载了对应插件，且聊天窗口收到模型回复。

## 常见报错

- **401 Unauthorized**　确认已替换示例密钥，检查插件正在读取的配置文件，以及密钥是否与地址匹配。密钥有变更时重启再试。
- **404 Not Found**　查看实际请求路径。ChatGPT Turbo 的 `oneapi_url` 填到 `/v1`，白泽的 `AICHAT_API_URL` 填到 `/v1/chat/completions`。看到重复的 `/v1` 或 `/chat/completions` 时，重新核对对应插件要求的地址。
- **模型不存在**　核对 `oneapi_model` 或 `AICHAT_MODEL_ID` 的完整拼写，以及当前密钥是否允许使用该模型。服务商调整模型后，用它当前提供的对话模型 ID。
- **请求超时**　从 NoneBot2 所在主机或容器检查网络，并用短文本重试。白泽的模型请求超时配置是 `AICHAT_REQUEST_TIMEOUT`，单位是秒。连接能建立、只有等回复超时的时候，再考虑调整这个值。
