---
title: "Codex 报错 429 / 403 DAILY_LIMIT_EXCEEDED / WEEKLY_LIMIT_EXCEEDED 怎么解决"
slug: "codex-daily-weekly-limit-exceeded-429-403"
description: "区分 Codex 报错 DAILY_LIMIT_EXCEEDED / WEEKLY_LIMIT_EXCEEDED（套餐周期限额）与瞬时限流（rate_limit_error），并提供不中断开发的切换与恢复步骤。"
keywords:
  - Codex DAILY_LIMIT_EXCEEDED
  - Codex WEEKLY_LIMIT_EXCEEDED
  - daily usage limit exceeded Codex
  - weekly usage limit exceeded Codex
  - Codex 429 403 限额
error_codes: ["429", "403"]
date: "2026-11-25"
category: "codex-troubleshooting"
canonical_path: "/daily/guides/codex/codex-daily-weekly-limit-exceeded-429-403/"
aff_code: "UG937JQ67MRS"
---

# Codex 报错 `429` / `403` `DAILY_LIMIT_EXCEEDED` / `WEEKLY_LIMIT_EXCEEDED` 怎么解决

高频使用 Codex 做全仓重构、多轮工具调用或自动化脚本时，经常会遇到 `429` 或 `403` 的限额提示。这类报错与临时服务器拥堵不同，反复重试通常不会立刻恢复。

## 报错现象

终端中出现以下任一原文：

- `429 api_error`: `DAILY_LIMIT_EXCEEDED`（`daily usage limit exceeded`）或 `WEEKLY_LIMIT_EXCEEDED`（`weekly usage limit exceeded`）
- `403 billing_error`: `daily usage limit exceeded` 或 `weekly usage limit exceeded`

## 30 秒定位根因

请先把它和瞬时限流区分开：

- **本错误（`DAILY_LIMIT_EXCEEDED` / `WEEKLY_LIMIT_EXCEEDED`）**：你当前所用的订阅套餐或 Key 配置的**每日 / 每周额度配额**已经用满。在周期重置前，继续用同一个套餐分组的 Key 重试仍会被拒绝。
- **对比瞬时限流（`rate_limit_error`）**：如果报错类型是 `rate_limit_error`（提示请求速率受限），那属于上游并发/速率抖动，等 5–30 秒即可恢复；而日/周限额属于配额上限。

此外，如果单个长会话上下文非常庞大，每发一句都会把几十万 token 的历史重新送给模型，也会比平时快得多地吃光日/周额度。

## 精确修复步骤（全服务商通用）

### 步骤 1：确认是否可等待自动重置或切换按量 Key

1. 登录你的服务商控制台，查看当前套餐的日限额 / 周限额重置时间；
2. 若手头任务需要立刻继续，可以：
   - 切换为**按量计费分组的 API Key**（按用途分别建 Key，临时顶上）；或
   - 升级到更高档位的订阅套餐。
3. 如切换了 Key，记得同步更新 `~/.codex/auth.json`（Windows 为 `%userprofile%\.codex\auth.json`）并重启 Codex：

```json
{
  "OPENAI_API_KEY": "sk-切换后的API_Key"
}
```

### 步骤 2：避免单个长会话过快消耗配额

恢复后，建议同步优化日常用法，降低单日 token 消耗：

1. 在 Codex 中完成一个子任务后，执行 `/compact` 压缩历史上下文，或直接新开会话；
2. 避免把整仓日志、构建产物或无关大文件直接贴进对话；
3. 检查是否给单个 Key 设了过低的自定义日限额（部分平台支持在密钥设置里手动限制每日消费上限）。

---

## 延伸参考：按量与月卡灵活切换

如果你的开发强度在平时与冲刺期波动较大，可以在支持**按量或月卡**的路由平台上**按用途分别建 Key**，平时走月卡、冲刺期平滑切到按量，避免卡在周期限额上：

- Codex 接入文档与配置指南：[https://router.nanafox.com/docs](https://router.nanafox.com/docs)
- 注册体验 NanaFox Router（Codex 专向入口）：[https://router.nanafox.com/register?aff=UG937JQ67MRS&use=codex](https://router.nanafox.com/register?aff=UG937JQ67MRS&use=codex)
