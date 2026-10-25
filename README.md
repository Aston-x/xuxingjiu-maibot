# Xuxingjiu · MaiBot edition (许杏玖 · MaiBot 版)

> The successor to [`Aston-x/xuxingjiu`](https://github.com/Aston-x/xuxingjiu) (the v1.2 monolith).
> Same character, new spine: the QQ protocol end was replaced, and the brain now runs on
> [MaiBot](https://github.com/Mai-with-u/MaiBot) instead of our own hand-rolled runtime.

[English](README.md) · [中文](README.zh-CN.md)

---

## Why the rewrite happened

This is the part worth reading. Three problems chained into each other.

### 1. NapCat was too easy to get the account banned

Our v1.2 stack drove QQ through **NapCat**. NapCat works by *replacing QQ's own Electron
entry point* — `qqnt.json`'s `"main"` is swapped for `./loadNapCat.js`, and `napcat.mjs` takes
over from there. The consequence is that **QQ's main-process code never executes**: no
windows, no message bubbles, no taskbar flash. That is exactly why NapCat can be truly
silent — it isn't hiding the UI, the UI code simply never runs.

But the same mechanism is the risk: the account is no longer running a normal QQ client,
and the protocol traffic is far from what Tencent's risk engine expects. Accounts on this
stack get banned, and the ban is the whole project gone — the character, the memory, the
diary, all of it lives in that one QQ number.

### 2. So the control end was replaced — but the replacement is closed-source

The fix was to stop replacing QQ's entry point and start **hooking** it instead. That is
**SnowLuma**: QQ's full desktop UI keeps running exactly as normal (so the human-facing
account stays a real, ordinary QQ client), and only a hook is injected to expose a OneBot
v11 endpoint for the bot side.

The cost: SnowLuma's hook is a **closed native binary**
(`native/snowluma-win32-x64.dll` / `.node`), and its licence states plainly that the
native add-on is proprietary and outside the source licence. So the thing that carries
our messages **cannot be inspected, patched, or recompiled by us**. A protocol-end we
cannot fix is a protocol-end we cannot own.

### 3. So the brain had to become open too — and that is why MaiBot

Our v1.2 brain (`qqbot/`) was our own code, which is nice until you count what it
implies: we owned the OneBot client, the plugin system, model dispatch, the memory
kernel, the WebUI, the planner, the expression system — and every upstream QQ change
landed on us as a bug to fix in our own codebase, alone.

**MaiBot** is GPL-3.0, actively maintained, and already solves the parts we would have
had to keep writing: a plugin SDK, a 400+ entry plugin marketplace, a two-layer memory
kernel with session-scoped retrieval, a planner/replier split, and a WebUI. And it speaks
OneBot v11, so **SnowLuma (or NapCat) can be swapped underneath it without touching the
character**.

So the rewrite was not "we gave up on our project". It was: *the layer that talks to
QQ must be something we can own; the layer that thinks should be something we do not
have to maintain alone.* The character, the persona, the memory layout and the privacy
rules all carried over unchanged — they were never the problem.

### Why MaiBot and not our own monolith, concretely

| | our v1.2 monolith | MaiBot |
|---|---|---|
| QQ protocol end | we owned it (and the ban risk) | swapped to SnowLuma; MaiBot only speaks OneBot v11 |
| plugin ecosystem | we wrote everything, including the diary plugin | 400+ plugins on the marketplace; we deleted our hand-written diary plugin and used the official one |
| memory | our own JSON store | A_Memorix: two-layer retrieval, **session-scoped by design**, summarisation, decay policy |
| upgrades | every upstream QQ change was our bug | follow upstream `dev`; `v1.3.9 → v1.3.14` during this rewrite alone |
| licence | GPL-3.0 | GPL-3.0 |

The v1.2 tree is kept alive and archived at
[`Aston-x/xuxingjiu`](https://github.com/Aston-x/xuxingjiu) (tag
`archive-开源v1.3支线-20260929-已被桌宠重构线取代`). It is a working, readable
reference for the character and the QZone bridge.

---

## What this repository contains

Deliberately minimal — **no accounts, no cookies, no API keys, no chat logs, no diary
entries, no persona text.**

```
config/     sanitized config templates (every secret is "")
patches/    the four patches this deployment needs on top of upstream MaiBot
scripts/    launch + environment-check scripts (paths are placeholders)
docs/       the rewrite rationale, architecture, and patch notes
```

The character itself, the memory design, the privacy isolation rules and the
voice-pipeline write-ups live in the deployment repo, not here.

---

## The four patches

All four are small and local. See [`docs/插件补丁说明.md`](docs/插件补丁说明.md).

1. `core-platform-io-group-target-fallback.patch` — a group chat's outbound message does
   not always carry `group_info` (plugin-triggered proactive messages don't). The original
   code then classified it as `chat_type=private` with an empty target, and
   `adapter_policy` dropped it as `missing_target_id` — **the chat visibly stalled for
   40–50 seconds, nine times a day**. The patch falls back to the inherited
   `platform_io_target_group_id`.
2. `core-memory-summary-filter.patch` — the summariser now drops bot messages and
   command messages, so system notices stop feeding back into her own memory.
3. `plugin-impression-card-session-scope.patch` — the impression card was stored **per
   person, shared across every chat**. Private-chat details therefore leaked into group
   context (the group's planner literally read "20块, 私聊黏人, 四个赞, 炸鸡"). Cards are
   now keyed `person_id#session_id`.
4. `plugin-better-diary-continuity-scope.patch` — the cross-day "continuity" state was one
   global file, so a diary written from private material leaked into the next group's
   diary and got published to a public feed. Continuity is now bucketed per
   `target_chats`.

---

## Deploy

```bash
git clone https://github.com/Aston-x/xuxingjiu-maibot
cd xuxingjiu-maibot

# 1. MaiBot core (GPL-3.0)
git clone https://github.com/Mai-with-u/MaiBot.git
cd MaiBot && uv sync && uv run python bot.py

# 2. config: copy the templates and fill in every <placeholder>
cp ../../config/bot_config.example.toml   config/bot_config.toml
cp ../../config/model_config.example.toml config/model_config.toml

# 3. apply the patches you need
git apply /path/to/xuxingjiu-maibot/patches/core-platform-io-group-target-fallback.patch

# 4. a OneBot v11 endpoint (SnowLuma or NapCat) + your model API keys
```

`scripts/check_env.py` verifies the ports, the plugin load count and whether every
credential you left blank is still blank.

---

## Notices

- **No secrets, ever.** `config/*.example.toml` ships with empty credentials and
  placeholder IDs. The QZone bridge in the v1.2 repo is reverse-engineered; using it may
  violate Tencent's terms of service. See [`NOTICE.md`](NOTICE.md).
- The voice pipeline (GPT-SoVITS) trains on **fan-uploaded** audio clips; this repository
  ships **no audio data and no model weights** — only the recipe.
- Xuxingjiu is a fictional cat-girl. Any resemblance to a real person is a coincidence.

## License

[GPL-3.0](LICENSE) — same as MaiBot.
