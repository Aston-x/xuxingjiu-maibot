# Telegram 迁移说明

> 更新时间：2026-11-10
>
> 当前决定不是“立刻关掉 QQ”。SnowLuma 已转私有且不再更新，但现有 QQ 机器人暂时保留；
> Telegram 先以并行适配器接入，验收通过后再决定是否收缩 QQ 侧。

维护者 Telegram：[`@jiyi2519`](https://t.me/jiyi2519)

这个链接是维护者主页，不是机器人身份，也不能替代 Bot Token 或数字用户 ID。

当前 Bot：[`@xuxingjiu_bot`](https://t.me/xuxingjiu_bot)（2026-11-10 创建并完成私聊实机验收）。

## 适配器选择

| 方案 | 宿主要求 | 当前结论 |
|---|---|---|
| [`exynos967/MaiBot-Telegram-Adapter`](https://github.com/exynos967/MaiBot-Telegram-Adapter) | MaiBot 1.0~1.9；SDK 2.0+ | **第一阶段使用**；当前 MaiBot 1.3.9 可直接加载 |
| [`Mai-with-u/Maibot-telegram-adaptor`](https://github.com/Mai-with-u/Maibot-telegram-adaptor) | MaiBot >= 1.3.18；SDK >= 2.19 | 功能更完整，但升级宿主前不能直接接入 |

第一阶段锁定兼容版的提交
`25a0183d9af86341a8d12df2c4c3f4984143e162`，先验证最关键的私聊收发。
等 MaiBot 核心完成升级、四个本机核心补丁重新验收后，再评估官方适配器。

本机还补了一个很小的可靠性补丁：

- `getUpdates` 的 offset 按机器人账号持久化到宿主插件数据目录；
- 更新按顺序处理，路由调用结束后才推进 offset；
- 宿主侧消息 ID 加 `chat_id:` 前缀，避免不同聊天的局部消息编号冲突。

可重放补丁在部署备份 `_插件安装备份\exynos967_telegram-adapter.offset-persistence.20261110.patch`。
它解决的是重启重放与边界消息丢失，不等价于官方新版适配器的完整失败队列。

## 双栈拓扑

```text
QQ 桌面端 -> SnowLuma -> OneBot v11 --------+
                                            +-> 同一个 MaiBot
Telegram Bot API <-HTTPS 长轮询-> TG adapter +->
```

- QQ 的 platform 仍是 `qq`，Telegram 的 platform 是 `telegram`。
- 两边的账号 ID、会话 ID、消息 ID 分开；不按显示名跨平台合并。
- memfade 以宿主 `session_id` 隔离作用域，Telegram 私聊和群聊会自然形成新作用域。
- **默认不迁移旧私聊记忆到 Telegram**。如果以后要迁移，只迁白名单内、逐条审核过的数据，
  不把 QQ 群聊和私聊混在一张卡或一个共享桶里。

## 接入步骤

### 1. 安装但保持关闭

```powershell
git clone https://github.com/exynos967/MaiBot-Telegram-Adapter.git plugins/exynos967_telegram-adapter
git -C plugins/exynos967_telegram-adapter checkout 25a0183d9af86341a8d12df2c4c3f4984143e162
```

插件放在 MaiBot 的 `plugins/` 下，使用仓库自带配置模板，
或参考本仓库的 [`config/telegram-adapter.example.toml`](../config/telegram-adapter.example.toml)。

安全默认值：

- `plugin.enabled = false`
- `telegram_bot.token = ""`
- 群聊和私聊都是 `whitelist`
- 两个白名单都为空，表示暂时不接收任何 Telegram 消息

网络实测：Windows `curl.exe`/schannel 在 Nano TUN 下会出现 TLS 握手失败，
但 MaiBot 插件使用的 Python/httpx 与只读探针可以正常访问 Bot API。
2026-11-10 已用 `proxy_enabled = false` 完成 `getMe`、`getUpdates` 和私聊收发，
因此当前不要求额外代理；以后更换网络环境时再重新验收。

### 2. 创建 Bot 并拿到数字身份

1. 在 Telegram 找 `@BotFather`，执行 `/newbot`。
2. 把 Token 只填进本机插件 `config.toml`，不要提交到 Git、日志或截图里。
3. 启动插件后，从日志的 `Telegram Bot: id=...` 取得机器人数字 ID。
4. 把机器人加入 MaiBot 的 `[bot].platforms`，例如 `telegram:<bot数字ID>`。
5. 机器人若配置过 Webhook，先移除 Webhook；长轮询不能和 Webhook 同时工作。

### 3. 获取维护者数字 ID

先给机器人发 `/start`，再用 Bot API 的 `getUpdates` 或适配器日志确认发送者的数字 ID。
**不要把 `@username` 当授权凭据**：Telegram 的用户名可以改，白名单应使用稳定的数字 ID。

仓库提供了一个只读探针，不会打印 Token，也不会推进 offset。插件保持关闭时运行：

```powershell
<MaiBot>\.venv\Scripts\python.exe <xuxingjiu-maibot>\scripts\telegram_probe.py `
  --plugin-config <MaiBot>\plugins\exynos967_telegram-adapter\config.toml
```

它会输出 Bot 数字 ID、待处理私聊的用户 ID 和群 `chat_id`，可直接用于白名单候选。

拿到后进行最小放行：

```toml
[chat]
private_list_type = "whitelist"
private_list = ["<维护者数字ID>"]
group_list_type = "whitelist"
group_list = []
```

群聊先全部关闭。私聊验收通过后，再逐个加入允许的群 `chat_id`。

### 4. 启用并验收

把 `plugin.enabled` 改成 `true`，保存后由插件热重载。依次验证：

- 非白名单用户发消息被丢弃；
- 维护者私聊能收能回；
- QQ 原有私聊和群聊不中断；
- Telegram 重启后能从已确认 offset 继续收消息；
- 图片与回复引用至少各测一次；
- 确认日志和配置文件里都没有打印 Token。

### 5. 再考虑收缩 QQ

至少完成一轮稳定性观察后再决定是否停用 SnowLuma。
停用 QQ 前要单独处理 QQ 空间、群管理、戳一戳等平台专属能力；
这些能力不能假装在 Telegram 上仍然存在。

## 回滚

第一阶段不改 QQ 配置，因此回滚只需：

1. 把 Telegram 插件 `plugin.enabled` 改回 `false`；
2. 恢复插件 `config.toml` 的上一份备份；
3. 确认 SnowLuma 的 3000/3001 与 MaiBot 的 8001 仍在原状态。

不要用删除 QQ 数据、清空 memfade 库或重建宿主机的方式“回滚”。

## 尚未完成

- [x] 获取 BotFather Token 与机器人数字 ID
- [x] 机器人在 `getMe`、长轮询和私聊回复链路通过验收
- [x] 建立首个 Telegram 私聊白名单并验证未知用户会被丢弃
- [ ] 让维护者主号 `@jiyi2519` 向 Bot 发送 `/start`，取得数字 ID 后加入白名单
- [ ] 决定群聊第一批白名单
- [ ] 评估官方适配器所需的 MaiBot 升级与核心补丁重打
- [ ] 为 QQ 空间、群管理、戳一戳等平台专属功能建立 Telegram 对应方案或明确下线

