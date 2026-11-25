---
title: "Codex 报错 400 Your input exceeds the context window of this model 怎么修"
slug: "codex-input-exceeds-context-window-400"
description: "解决 Codex 报错 400 invalid_request_error: Your input exceeds the context window of this model，掌握 /compact 压缩、会话拆分及自定义 provider 避免长会话压缩卡死的避坑技巧。"
keywords:
  - Your input exceeds the context window of this model
  - Codex 400 context window
  - Codex 上下文超限
  - Codex compact 命令
  - Codex remote compaction v2
error_codes: ["400"]
date: "2026-11-25"
category: "codex-troubleshooting"
canonical_path: "/daily/guides/codex/codex-input-exceeds-context-window-400/"
aff_code: "UG937JQ67MRS"
---

# Codex 报错 `400` `Your input exceeds the context window of this model` 怎么修

在一个 Codex 会话里连续改了十几个文件、或者直接粘贴了整段构建日志之后，经常会突然撞上模型上下文窗口上限，返回 `400` 报错。

## 报错现象

终端或客户端返回：

- `400 invalid_request_error`: `Your input exceeds the context window of this model. Please adjust your input and try again.`

## 30 秒定位根因

核心原因很直接：**本次请求携带的完整内容（系统提示词 + 历史多轮对话 + 工具返回的文件内容/日志 + 你刚输入的消息）总 token 数超过了当前模型允许的最大上下文窗口。**

常见触发场景：
1. 同一个会话连续聊了很久，中间包含大量代码 diff、测试输出或长日志文件；
2. 一次性往输入框里粘贴了数千行报错堆栈、JSON 响应或构建日志；
3. 自定义 provider 在 `config.toml` 里把 `name` 写成了 `"OpenAI"`，导致 Codex 在接近上下文阈值时尝试走官方专属的 remote compaction v2，而第三方端点不支持该控制协议，结果自动压缩失败、上下文越积越大最终超窗卡死。

## 精确修复步骤（全服务商通用）

### 步骤 1：在当前会话执行 `/compact` 压缩历史

如果还能在当前会话输入命令，先直接运行：

```text
/compact
```

Codex 会将之前的对话历史摘要为紧凑的上下文，释放大量 token 空间。

### 步骤 2：如果已经压不动，直接新开会话并精准投喂上下文

当单条最新输入或已有历史已经超过窗口极限、连 `/compact` 都无法发出时：

1. 新开一个 Codex 会话；
2. 用 2–3 句话总结当前进度与目标，只附带**当前需要修改的那几个具体文件路径**；
3. 对于超长日志，先用 `tail -n 100` 或 `grep` 截取关键报错片段再贴给 Codex，不要把几 MB 的完整日志直接塞进对话。

### 步骤 3：自定义 provider 避坑（防止自动压缩失效）

如果你使用的是第三方自定义端点，检查 `~/.codex/config.toml` 中的 `[model_providers.<id>]`，**不要把 `name` 写成 `"OpenAI"`**，改成任意自定义名称（例如 `name = "custom-relay"`）：

```toml
model_provider = "custom"

[model_providers.custom]
name = "custom-relay"
base_url = "https://你的服务商端点"
wire_api = "responses"
requires_openai_auth = true
```

这样长会话触发自动压缩时会正常走本地 compaction，不会因为触发官方 remote compaction v2 而卡死。

---

## 延伸参考：Codex 配置模板与排错指南

如需对照完整的 Codex `config.toml` 标准写法，或查看与 CC Switch 配合使用的配置步骤，可以参考 NanaFox Router 文档：

- Codex 标准接入文档：[https://router.nanafox.com/docs](https://router.nanafox.com/docs)
- 注册体验 NanaFox Router（Codex 专向入口）：[https://router.nanafox.com/register?aff=UG937JQ67MRS&use=codex](https://router.nanafox.com/register?aff=UG937JQ67MRS&use=codex)
