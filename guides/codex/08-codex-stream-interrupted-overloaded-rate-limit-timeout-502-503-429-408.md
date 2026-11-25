---
title: "Codex 报错 502 流式中断 / 503 overloaded / 429 rate_limit_error / 408 请求超时怎么修"
slug: "codex-stream-interrupted-overloaded-rate-limit-timeout-502-503-429-408"
description: "快速区分 Codex 常见的 502 Upstream response stream was interrupted、503 overloaded、429 rate_limit_error 与 408 Timed out reading request body，按根因分别处理。"
keywords:
  - Upstream response stream was interrupted Codex
  - Upstream HTTP/2 stream failed Codex
  - Codex 503 overloaded
  - Codex 429 rate_limit_error
  - Timed out reading request body 408 Codex
error_codes: ["502", "503", "429", "408"]
date: "2026-11-25"
category: "codex-troubleshooting"
canonical_path: "/daily/guides/codex/codex-stream-interrupted-overloaded-rate-limit-timeout-502-503-429-408/"
aff_code: "UG937JQ67MRS"
---

# Codex 报错 `502` 流式中断 / `503` overloaded / `429` `rate_limit_error` / `408` 请求超时怎么修

在 Codex 长输出生成代码、或者高峰期连续调用时，终端偶尔会突然断开并报 `502`、`503`、`429` 或 `408`。这几个状态码看起来都像“连不上”，但其实分为**上游瞬时波动**和**本地上传超时**两类，处理方式完全不同。

## 报错现象

终端或日志中出现以下任一原文：

- `502`: `Upstream response stream was interrupted` / `Upstream HTTP/2 stream failed` / `Upstream service temporarily unavailable`
- `503 service_unavailable_error`: `Our servers are currently overloaded. Please try again later.`
- `429 rate_limit_error`: `Rate limit reached / temporarily rate-limited. Please retry later.`
- `408 invalid_request_error`: `Timed out reading request body`

## 30 秒定位根因

用状态码一秒分流：

1. **`502` 流中断 / `503` 过载 / `429 rate_limit_error`**：属于**上游模型接口短暂抖动、HTTP/2 长连接断开或高峰期瞬时限流**。你的本地 `config.toml` 和 Key 通常是正常的，不需要急着改配置。
2. **`408 Timed out reading request body`**：属于**服务端在规定时间内没收完你的请求体**，多半是本地网络/代理链路不稳定，或者单次会话携带了过大的请求体（例如粘贴了几 MB 的日志或图片），导致上传过慢超时。

## 精确修复步骤（全服务商通用）

### 情况 A：遇到 `502` / `503` / `429 rate_limit_error`

1. **不要立刻反复狂点重试**，等待 **5–30 秒**后再重新发送一次请求，绝大多数瞬时抖动都会自动恢复；
2. 如果正在跑自动化脚本，给 `502` / `503` / `429` 加上带随机抖动的指数退避重试（例如 5s → 15s → 30s）；
3. 如果某一条长输出反复在同一处触发 `HTTP/2 stream failed`，可以先把大任务拆成两个小步骤，缩短单次流式连接时长；
4. 若连续多次重试仍持续报错，前往你的服务商控制台查看服务状态公告或联系技术支持。

### 情况 B：遇到 `408 Timed out reading request body`

1. **检查本地网络与代理稳定性**：如果你挂了本地代理，确认节点丢包率与上传带宽正常，避免经过多跳不稳定代理；
2. **精简单次请求体积**：
   - 在 Codex 中运行 `/compact` 缩减历史上下文体积；
   - 不要一次性往对话框里粘贴几 MB 的日志文件或大量高分辨率截图；
3. 如果怀疑是本地代理链路不稳定，尝试切换更稳定的节点或关闭无关代理测试上传速度。

---

## 延伸参考：Codex 接入与排错文档

如果你希望排查是否是本地代理链路导致的流式中断，或需要原生 Responses 接口的标准参考配置，可以查看 NanaFox Router 的接入文档（支持按用途建 Key，并可一键导入 CC Switch）：

- Codex 标准接入文档：[https://router.nanafox.com/docs](https://router.nanafox.com/docs)
- 注册体验 NanaFox Router（Codex 专向入口）：[https://router.nanafox.com/register?aff=UG937JQ67MRS&use=codex](https://router.nanafox.com/register?aff=UG937JQ67MRS&use=codex)
