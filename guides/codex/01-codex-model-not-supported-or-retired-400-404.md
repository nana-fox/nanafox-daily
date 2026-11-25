---
title: "Codex 报错 model_not_found / not supported when using Codex（400 / 404）怎么修"
slug: "codex-model-not-supported-or-retired-400-404"
description: "解决 Codex CLI 与 Codex Desktop 报错 model_not_found、gpt-5.4 / gpt-5.5 已下线或模型不在当前分组支持列表的问题，30 秒定位根因并修复 config.toml。"
keywords:
  - Codex model_not_found
  - model is not supported when using Codex
  - Codex 404 model_not_found
  - Codex 400 invalid_request_error
  - gpt-5.5 retired Codex
  - Codex config.toml model
error_codes: ["400", "404"]
date: "2026-11-25"
category: "codex-troubleshooting"
canonical_path: "/daily/guides/codex/codex-model-not-supported-or-retired-400-404/"
aff_code: "UG937JQ67MRS"
---

# Codex 报错 `model_not_found` / `not supported when using Codex`（400 / 404）怎么修

在终端运行 Codex CLI 或使用 Codex Desktop 时，如果刚升级客户端、更换接口服务商，或沿用了旧的 `config.toml` 配置，很容易遇到模型不支持或已下线的 `400` / `404` 报错。

## 报错现象

终端或客户端日志中通常会出现以下几类原文之一：

- `400 invalid_request_error`: `The 'gpt-5.4' model is not supported when using Codex with a ChatGPT account.`（`gpt-5.4-mini`、`gpt-5.3-codex-spark`、`gpt-4o-realtime-preview`、`gpt-4o-audio-preview` 等旧模型名或非代码模型也会触发同类报错）
- `404 model_not_found`: `Model "gpt-5.5" targets GPT-5.5, which retired from Codex with ChatGPT sign-in on October 14, 2026. Select an available replacement such as GPT-6.1 Sol or GPT-6.2 Sol`
- `404 model_not_found`: `The model "xxx" does not exist or you do not have access to it`

## 30 秒定位根因

按以下 3 个方向快速排查，90% 以上都能立刻定位：

1. **填了已下线或当前通道不支持的模型名**：`~/.codex/config.toml` 里仍写着已经下线的旧模型名，或填了实时语音/音频等不适用于 Codex 的模型。
2. **API Key 分组与目标模型不匹配**：很多聚合/路由服务商会按模型厂商拆分分组（例如 OpenAI GPT 分组与 Anthropic Claude 分组分离），拿 GPT 分组的 Key 去调用 Claude 或其他平台模型时，就会返回 `404 model_not_found` 或无权限提示。
3. **Codex Desktop 26.1117+ 前端覆盖了默认模型**：新版 Codex Desktop 新建会话时会校验内置模型目录，若自定义模型不在内置目录中且未配置 `model_catalog_json`，前端可能会强行回退到内置默认模型，导致发往第三方端点时触发 `model_not_found`。

## 精确修复步骤（全服务商通用）

### 步骤 1：更新 `~/.codex/config.toml` 中的 `model`

打开 `~/.codex/config.toml`（Windows 路径为 `%userprofile%\.codex\config.toml`），将 `model` 替换为当前通道实际支持的模型名称（例如 `gpt-6.1-sol` 或 `gpt-6.2-sol`）：

```toml
model_provider = "custom"
model = "gpt-6.1-sol"

[model_providers.custom]
name = "custom"
base_url = "https://你的服务商端点"
wire_api = "responses"
requires_openai_auth = true
```

保存后**彻底退出并重启** Codex CLI / Desktop。

### 步骤 2：核对 API Key 所属分组（按用途分别建 Key）

如果报错提示 `404 model_not_found` 或当前 Key 无权访问该模型：

1. 登录你的 API 服务商控制台，检查 `~/.codex/auth.json` 里填写的 Key 属于哪个模型分组；
2. 确认该分组是否包含你要调用的模型；若需要分别使用 GPT/Codex 与 Claude 等不同生态模型，请**按用途分别创建对应分组的 Key**，不要混用；
3. 更新 `~/.codex/auth.json` 后重启客户端。

### 步骤 3：排查 Codex Desktop 新建会话模型回退（如适用）

如果你在 Codex CLI 中运行正常，仅在 Codex Desktop（26.1117+）新建会话时触发 `model_not_found`：

1. 临时用终端 `codex -m <模型名>` 验证端点本身是否正常；
2. 如需在 Desktop 中使用非内置目录的自定义模型，可在 `~/.codex/` 下配置最小 `model_catalog_json` 并在 `config.toml` 顶层引入，或直接使用上游支持的最新标准模型名。

---

## 延伸参考：省去手改配置的接入方式

如果你希望直接对照标准 `config.toml` 与 `auth.json` 配置模板，或使用支持 Codex 原生 Responses 接口的路由服务，可以查看 NanaFox Router 的接入文档（支持按用途建 Key，并可一键导入 CC Switch）：

- 接入文档与配置模板：[https://router.nanafox.com/docs](https://router.nanafox.com/docs)
- 注册体验 NanaFox Router（Codex 专向入口）：[https://router.nanafox.com/register?aff=UG937JQ67MRS&use=codex](https://router.nanafox.com/register?aff=UG937JQ67MRS&use=codex)
