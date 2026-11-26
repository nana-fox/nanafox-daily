---
title: "AstrBot 怎么接入 OpenAI 兼容服务"
slug: "astrbot-openai-compatible"
description: "在 AstrBot 添加 OpenAI Compatible 对话提供商，填写 API Base URL 和密钥，选择模型并排查 401、404 和超时。"
keywords:
  - AstrBot OpenAI 兼容
  - AstrBot API Base URL
  - AstrBot 模型提供商
date: "2026-11-26"
category: "bot-integration"
---

# AstrBot 怎么接入 OpenAI 兼容服务

## 适用场景

AstrBot 已经运行，你想给内置 AI 对话接上一个支持 OpenAI Chat Completions 的服务。其中可以是模型厂商的兼容接口、自建网关或 NanaFox Router。先从服务商拿到 API 基础地址、API Key 和可用的对话模型 ID。

## 在 AstrBot 配置对话模型

1. 在管理面板打开「模型提供商 → 对话」，点击「新增」，选择 `OpenAI Compatible`。旧版入口和名称可能不同，以你的版本为准。[AstrBot 接入模型服务](https://docs.astrbot.app/providers/start.html)
2. 给提供商起一个便于识别的名称，填入 `API Key` 和 `API Base URL`。基础地址使用服务商给出的版本路径，例如 `https://api.example.com/v1`。AstrBot 会按协议请求具体端点。
3. 点击「保存并获取模型」，在目标模型旁点击 `+`，确认模型已启用。如果接口无法列出模型，先「保存配置」，再通过「自定义模型」填入完整模型 ID。点击「测试模型」，确认模型能返回内容。[AstrBot 的 OpenAI 兼容配置示例](https://docs.astrbot.app/providers/newapi.html)
4. 在「配置文件」中打开机器人实际使用的配置，进入「AI → 模型」，将「对话模型」设为刚添加的模型，点击「保存配置」。再发一句简短的文本消息，确认机器人也能回复。

## 以 NanaFox Router 为例

- 新用户进入接入引导，选择「Cherry Studio / Cursor 等客户端」，创建「OpenAI GPT」分组的 API Key。[打开 Router 客户端接入入口](https://router.nanafox.com/register?aff=UG937JQ67MRS&use=client&utm_source=nanafox_daily&utm_medium=site)
- 已有 Router 账号时，登录后从左侧「API 密钥」进入。已有「OpenAI GPT」分组的密钥可以直接复制使用。要新建，点「创建密钥」，填写「名称」，在「厂商」选「OpenAI」，在「分组」选「OpenAI GPT」，点「创建」，再从列表复制新密钥。

- `API Base URL` 填 `https://router.nanafox.com/v1`。
- `API Key` 填刚创建或已有的分组密钥。
- 在模型列表中选择 `gpt-6.1-sol`。使用「自定义模型」时也填这个模型 ID。若服务商调整了模型列表，以当前密钥可用的对话模型为准。

## 常见报错

- **401 Unauthorized**　先核对密钥是否完整、仍然有效，并确认密钥和基础地址来自同一个服务商。刚换过密钥时，保存提供商配置后再测一次。
- **404 Not Found**　查看日志中失败的 URL。Router 的基础地址以一个 `/v1` 结尾，对话请求应到 `/v1/chat/completions`。若路径重复或请求发到了 `/responses`，检查基础地址和提供商类型。
- **模型不存在**　如果返回体包含 `model_not_found`，先核对完整模型 ID 和密钥权限，再检查模型是否启用、当前配置文件是否选中了它。
- **请求超时**　先在 AstrBot 运行的主机或容器里检查到服务商的网络，再用「测试模型」发起短请求。如果单独测试通过、实际会话仍超时，试用新会话发一条短消息，并对照日志看请求卡在连接还是等回复。
