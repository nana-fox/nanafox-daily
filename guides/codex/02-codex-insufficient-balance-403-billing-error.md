---
title: "Codex 报错 403 insufficient balance / Insufficient account balance 怎么排查"
slug: "codex-insufficient-balance-403-billing-error"
description: "Codex CLI 与 Codex Desktop 出现 403 billing_error insufficient balance 或 Insufficient account balance 时，如何区分余额耗尽与分组 Key 填错并快速恢复。"
keywords:
  - Codex insufficient balance
  - Codex 403 billing_error
  - Insufficient account balance Codex
  - Codex auth.json Key 配置
error_codes: ["403"]
date: "2026-11-25"
category: "codex-troubleshooting"
canonical_path: "/daily/guides/codex/codex-insufficient-balance-403-billing-error/"
aff_code: "UG937JQ67MRS"
---

# Codex 报错 `403 insufficient balance` / `Insufficient account balance` 怎么排查

使用 Codex CLI 或 Codex Desktop 接入第三方 API 接口时，遇到 `403` 余额不足提示并不一定都是“账户里没钱了”，也经常发生在**开通了订阅/月卡却仍在使用旧的按量分组 Key** 的场景里。

## 报错现象

终端或日志中出现以下任一原文：

- `403 billing_error`: `insufficient balance`
- `403 api_error`: `Insufficient account balance`

## 30 秒定位根因

只需要确认两件事即可定位：

1. **当前账户的按量余额或体验额度已耗尽**：发起请求时所绑定的计费钱包余额不足以覆盖本次调用。
2. **本地 `auth.json` 仍在使用旧分组的 Key**：例如你在控制台已经开通了月卡/订阅套餐，但 `~/.codex/auth.json`（或环境变量 `OPENAI_API_KEY`）里还填着之前按量分组的 Key，系统就会继续扣按量钱包余额，从而报 `insufficient balance`。

## 精确修复步骤（全服务商通用）

### 步骤 1：确认生效的是哪一个 API Key

Codex 客户端同时可能读取 `~/.codex/auth.json` 和当前终端的环境变量。请先检查两处：

```bash
# 1. 检查环境变量是否设置了 OPENAI_API_KEY（仅输出长度与前4后4位脱敏预览，不打印完整密钥）
if [ -n "$OPENAI_API_KEY" ]; then
  printf 'OPENAI_API_KEY 已设置（长度 %d，预览 %s...%s）\n' "${#OPENAI_API_KEY}" "${OPENAI_API_KEY:0:4}" "${OPENAI_API_KEY: -4}"
else
  echo "OPENAI_API_KEY 未设置"
fi

# 2. 安全核对 ~/.codex/auth.json 中的 Key（仅显示字段名与前4后4位，不打印完整凭据）
# Windows 路径：%userprofile%\.codex\auth.json
python3 -c 'import json, pathlib; d = json.loads(pathlib.Path("~/.codex/auth.json").expanduser().read_text()); k = d.get("OPENAI_API_KEY", ""); print("keys:", list(d.keys()), "OPENAI_API_KEY:", (k[:4] + "..." + k[-4:] + f" (len={len(k)})") if len(k) >= 8 else ("<已设置>" if k else "<未设置>"))'
```

如果终端环境变量里残留了旧 Key，请先在 shell 配置文件（`.zshrc` / `.bashrc` 或系统环境变量）中清除或同步更新。

### 步骤 2：核对 Key 所属分组与账户计费状态

1. 登录你的 API 服务商控制台，核对当前账户余额与已生效的套餐/月卡状态；
2. 若按量余额确实耗尽，请补充余额或切换到已开通的有效套餐；
3. 若已开通套餐仍报 `insufficient balance`，请在控制台「API 密钥」页面核对刚才查到的 Key 是否绑定到了**对应套餐分组**——不同计费模式或模型分组通常需要**按用途分别建 Key**。

### 步骤 3：更新 `~/.codex/auth.json` 并重启 Codex

将确认无误的 Key 写入 `~/.codex/auth.json`：

```json
{
  "OPENAI_API_KEY": "sk-你的有效分组API_Key"
}
```

保存后彻底退出并重新启动 Codex（如果使用 CC Switch 管理配置，请在 CC Switch 内重新应用配置以确保文件已写入）。

---

## 延伸参考：标准 Codex 配置与接入文档

如果你需要核对 Codex 的标准 `config.toml` / `auth.json` 写法，或正在寻找支持按量与月卡、且支持按用途建 Key 的 Codex 路由服务，可参考 NanaFox Router 官方文档：

- 接入文档与排错说明：[https://router.nanafox.com/docs](https://router.nanafox.com/docs)
- 注册体验 NanaFox Router（Codex 专向入口）：[https://router.nanafox.com/register?aff=UG937JQ67MRS&use=codex](https://router.nanafox.com/register?aff=UG937JQ67MRS&use=codex)
