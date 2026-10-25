# 安全说明

## 这个仓库里应该永远不出现的东西

如果你要往这个仓库提交任何东西，先确认下面这些**一个都没有**：

- ❌ 任何 API key（MiniMax / DeepSeek / DashScope / OpenAI 兼容）
- ❌ QQ 登录 cookie（`p_skey` / `skey` / `cookies.json`）
- ❌ 真实 QQ 号、群号、session_id
- ❌ `MaiBot.db`（全部聊天记录，含私聊）
- ❌ 日记存档（`diaries.json`、`continuity-*.json`）
- ❌ 人设文本（`[personality]` 三段）
- ❌ 语音模型权重与训练音频素材

`scripts/check_env.py` 会扫 `config/*.example.toml`，发现非空凭据或真实 QQ 号会直接报 FAIL。
提交前跑一次：

```bash
python scripts/check_env.py
```

## 凭据怎么配

**不要把密钥写进任何会被 git 追踪的文件。** 两种做法：

1. **环境变量**（推荐）：在 `config/model_config.toml` 里留空
   `api_key = ""`，由 MaiBot 的 `api_providers[].api_key` 从环境注入；
2. **本地私有文件**：MaiBot 的 `config/` 与 `plugins/` 本来就在 `.gitignore` 里
   （`/config/*`、`/plugins/*`），实盘配置放那儿就天然不会被提交。

## 补丁里的注意事项

`patches/` 里的四个补丁是**源码级修改**，不含任何凭据，但它们揭示了本机的目录约定
（session_id 拼接方式、插件目录名等）。请在读之前确认这符合你的发布意图。

## 报告漏洞

发现安全问题请开 issue，或者直接联系维护者，不要在公开 issue 里贴密钥。
