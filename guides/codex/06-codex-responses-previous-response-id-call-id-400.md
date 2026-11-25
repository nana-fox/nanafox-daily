---
title: "Codex 报错 400 function_call_output requires call_id / previous_response_id 与 wire_api 不兼容怎么修"
slug: "codex-responses-previous-response-id-call-id-400"
description: "修复 Codex 报错 400 function_call_output requires call_id on HTTP requests; continuation via previous_response_id is only supported on Responses WebSocket v2，核对 wire_api、base_url 与客户端版本。"
keywords:
  - function_call_output requires call_id
  - previous_response_id Responses WebSocket v2
  - Codex wire_api responses
  - Codex 400 invalid_request_error
  - Codex base_url v1 404
error_codes: ["400", "404"]
date: "2026-11-25"
category: "codex-troubleshooting"
canonical_path: "/daily/guides/codex/codex-responses-previous-response-id-call-id-400/"
aff_code: "UG937JQ67MRS"
---

# Codex 报错 `400` `function_call_output requires call_id` / `previous_response_id` 与 `wire_api` 不兼容怎么修

在 Codex CLI 或 Codex Desktop 中执行多轮工具调用时，如果突然在 HTTP 请求上弹出关于 `call_id`、`previous_response_id` 和 `Responses WebSocket v2` 的 `400` 报错，说明客户端和接口之间的 **Responses 协议续传方式出现了不兼容**。

## 报错现象

终端或客户端日志出现以下完整原文：

- `400 invalid_request_error`: `function_call_output requires call_id on HTTP requests; continuation via previous_response_id is only supported on Responses WebSocket v2`

（同类配置问题下，如果 `base_url` 路径多写或少写了 `/v1`，或者填错了 `wire_api`，也可能伴随 `404` 接口不存在报错。）

## 30 秒定位根因

出现该报错通常由以下三个原因之一引起：

1. **Codex 客户端版本偏旧**：早期版本在 HTTP 降级模式下仍发送了依赖 WebSocket v2 续传（`previous_response_id`）的工具调用上下文，缺少 HTTP 模式要求的 `call_id` 配对字段。
2. **中间代理改写或降级了 Responses 请求**：本地流量经过了旧版中转代理（例如把 `/responses` 强行转写为旧版 `/chat/completions` 的代理工具），破坏了原生 Responses 协议结构。
3. **当前会话历史已被坏状态污染**：即便你刚改好了配置，旧会话里已经残留了不完整的续传上下文，继续在原会话里重试仍会反复报同一个 `400`。

## 精确修复步骤（全服务商通用）

### 步骤 1：将 Codex CLI / Desktop 升级到最新版本

先升级客户端，消除已知的协议降级 Bug：

```bash
# 若通过 npm 安装 Codex CLI
npm install -g @openai/codex@latest

# 检查当前版本
codex --version
```

Codex Desktop 用户请直接通过客户端内置更新或官网安装包升级到最新版。

### 步骤 2：核对 `~/.codex/config.toml` 的 `wire_api` 与 `base_url`

打开 `~/.codex/config.toml`（Windows 为 `%userprofile%\.codex\config.toml`），确保连接支持原生 Responses API 的端点：

```toml
model_provider = "custom"
model = "gpt-6.1-sol"

[model_providers.custom]
name = "custom"
base_url = "https://你的服务商端点"
wire_api = "responses"
requires_openai_auth = true
```

重点核对两项：
- `wire_api` 必须为 `"responses"`，不要经过会转写为 `chat/completions` 的旧代理；
- `base_url` **是否需要带 `/v1` 请严格以你所用服务商的官方文档为准**（有的服务商要求带 `/v1`，有的如 NanaFox Router 要求不带 `/v1`，填错会导致 `404`）。

### 步骤 3：新开一个干净的会话重试

修改配置并重启 Codex 后，**不要在已经报错的旧会话里继续追问**，直接新开一个会话重新发送任务，确认工具调用与续传恢复正常。

---

## 延伸参考：原生 Responses 接口接入文档

如果你需要连接原生支持 OpenAI Responses API 的路由端点，避免中间层协议转写导致的 `call_id` / `previous_response_id` 兼容问题，可以参考 NanaFox Router 的标准配置（`base_url = "https://router.nanafox.com"` 不带 `/v1`，`wire_api = "responses"`）：

- Codex 标准接入文档：[https://router.nanafox.com/docs](https://router.nanafox.com/docs)
- 注册体验 NanaFox Router（Codex 专向入口）：[https://router.nanafox.com/register?aff=UG937JQ67MRS&use=codex](https://router.nanafox.com/register?aff=UG937JQ67MRS&use=codex)
