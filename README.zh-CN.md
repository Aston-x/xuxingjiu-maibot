# 许杏玖 · MaiBot 版

> [`Aston-x/xuxingjiu`](https://github.com/Aston-x/xuxingjiu)（v1.2 单体版）的后继。
> 角色不变，骨架换新：**QQ 控制端换掉了，大脑从自研单体换成 [MaiBot](https://github.com/Mai-with-u/MaiBot)。**

[English](README.md) · [中文](README.zh-CN.md)

---

## 为什么要重写

这部分值得细看。三个问题一个牵出一个。

### 一、NapCat 太容易被封号

v1.2 那套是用 **NapCat** 驱动 QQ 的。NapCat 的原理是**替换 QQ 自己的 Electron 入口** ——
把 `qqnt.json` 的 `"main"` 换成 `./loadNapCat.js`，再由 `napcat.mjs` 接手。
后果是 **QQ 主进程代码根本不会执行**：没有窗口、没有消息气泡、没有任务栏闪烁。
这正是 NapCat 能做到「真静默」的原因 —— 它不是把窗口藏起来，而是那段 UI 代码压根没跑。

但同一个机制也是风险所在：账号不再是正常 QQ 客户端在跑，协议流量跟腾讯风控的预期差得很远。
这套架构下账号被封，封号就是整个项目没了 —— 人格、记忆、日记，全都长在那个 QQ 号上。

### 二、于是换掉了控制端 —— 但换来的这个是闭源的

解法是**不再替换 QQ 入口，改成 hook**。这就是 **SnowLuma**：QQ 的完整桌面 UI 照常跑
（人用的那个号还是个普普通通的桌面 QQ），只在旁边注入一个 hook，暴露 OneBot v11 给 bot 侧。

代价是：SnowLuma 的 hook 是**闭源原生二进制**
（`native/snowluma-win32-x64.dll` / `.node`），许可里明写「原生附加组件为专有组件，
不在源码许可范围内」。也就是说，**承载我们消息的那一层，我们看不见、改不了、也无法重新编译**。
一个改不了的控制端，就不是一个能自己掌控的控制端。

### 三、所以大脑也得换成开源的 —— 这才是选 MaiBot 的原因

v1.2 的大脑（`qqbot/`）是我们自己写的，这本来挺好，直到你数一数它意味着什么：
OneBot 客户端、插件系统、模型调度、记忆内核、WebUI、规划器、表达系统 —— 全是我们自己的代码，
而**QQ 每一次上游变动都变成我们要独自修的 bug**。

**MaiBot** 是 GPL-3.0、持续维护、而且把那些我们本来得继续写的东西都做完了：
插件 SDK、400+ 条的插件市场、带会话作用域的双层记忆内核、Planner/Replyer 分工、WebUI。
而且它讲 OneBot v11，所以 **SnowLuma（或 NapCat）可以在它下面随便换，不动角色一个字**。

所以这次重写不是「我们放弃了自己的项目」。而是：
*跟 QQ 说话的那一层必须是能自己掌控的；思考的那一层不该由我们一个人扛。*
角色、人设、记忆结构、隐私规则全都原样搬了过来 —— **它们从来不是问题所在**。

### 具体说，为什么是 MaiBot 而不是继续自研单体

| | 我们的 v1.2 单体 | MaiBot |
|---|---|---|
| QQ 控制端 | 自己扛（连带封号风险） | 换成 SnowLuma；MaiBot 只负责讲 OneBot v11 |
| 插件生态 | 全靠自己写，连日记插件都是手写的 | 市场 400+ 插件；手写日记插件直接删掉换官方 better-diary |
| 记忆 | 自己写的 JSON 存储 | A_Memorix：双层检索、**天生按会话隔离**、摘要化、衰减策略 |
| 升级 | QQ 上游每次变动都是我们的 bug | 跟上游 `dev`；光这次重写就从 v1.3.9 走到 v1.3.14 |
| 许可 | GPL-3.0 | GPL-3.0 |

v1.2 的代码树仍然活着，归档在
[`Aston-x/xuxingjiu`](https://github.com/Aston-x/xuxingjiu)
（tag `archive-开源v1.3支线-20260929-已被桌宠重构线取代`），
它是角色设计和 QZone bridge 的可读参考。

---

## 这个仓库里有什么

刻意做得很干净 —— **没有账号、没有 cookie、没有 API key、没有聊天记录、没有日记、没有人设文本**。

```
config/     脱敏配置模板（所有密钥都是空的）
patches/    这套部署在上游 MaiBot 之上需要的四个补丁
scripts/    启动脚本 + 环境体检脚本（路径都是占位符）
docs/       重写原因、架构、补丁说明
```

角色本身、记忆设计、隐私隔离规则、语音流水线的完整说明在部署仓库里，不在这里。

---

## 四个补丁

四个都很小、都很局部。详见 [`docs/插件补丁说明.md`](docs/插件补丁说明.md)。

1. `core-platform-io-group-target-fallback.patch` —— 群聊的出站消息**不一定带 `group_info`**
   （插件主动触发的那条就没有）。原代码于是把它判成 `chat_type=private` 且目标为空，
   `adapter_policy` 以 `missing_target_id` 直接丢弃 → **表现是聊天中途卡住 40~50 秒，一天 9 次**。
   补丁改成回退到已继承的 `platform_io_target_group_id`。
2. `core-memory-summary-filter.patch` —— 摘要器现在过滤掉 bot 消息与命令消息，
   系统通知不再回灌进她自己的记忆。
3. `plugin-impression-card-session-scope.patch` —— 印象卡片原本**按人存一份、所有会话共用**，
   于是私聊细节漏进群上下文（群里的 planner 直接读到了「20块, 私聊黏人, 四个赞, 炸鸡」）。
   现在卡片主键改成 `person_id#session_id`。
4. `plugin-better-diary-continuity-scope.patch` —— 跨天「连续性」状态原本是**一个全局文件**，
   从私聊取材写的日记会把私聊事实带进下一篇群日记，并跟着正文**公开发到空间**。
   现在连续性按 `target_chats` 分桶。

---

## 部署

```bash
git clone https://github.com/Aston-x/xuxingjiu-maibot
cd xuxingjiu-maibot

# 1. MaiBot 核心（GPL-3.0）
git clone https://github.com/Mai-with-u/MaiBot.git
cd MaiBot && uv sync && uv run python bot.py

# 2. 配置：复制模板，把每个 <占位符> 都填上
cp ../../config/bot_config.example.toml   config/bot_config.toml
cp ../../config/model_config.example.toml config/model_config.toml

# 3. 打上你需要的补丁
git apply /path/to/xuxingjiu-maibot/patches/core-platform-io-group-target-fallback.patch

# 4. 准备 OneBot v11 端（SnowLuma 或 NapCat）+ 你的模型 API key
```

`scripts/check_env.py` 会检查端口、插件加载数量，以及你留空的凭据是不是真的还空着。

---

## 声明

- **绝不含密钥。** `config/*.example.toml` 里凭据全是空串、ID 全是占位符。
  v1.2 仓库里的 QZone bridge 是逆向实现的，使用可能违反腾讯的服务条款，见 [`NOTICE.md`](NOTICE.md)。
- 语音流水线（GPT-SoVITS）训练用的是**网友上传**的音频素材；本仓库**不含任何音频与模型权重**，只给做法。
- 许杏玖是虚构的猫娘少女。

## 许可

[GPL-3.0](LICENSE) —— 与 MaiBot 一致。
