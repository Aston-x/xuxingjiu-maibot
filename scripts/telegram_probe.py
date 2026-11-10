# -*- coding: utf-8 -*-
"""Read-only Telegram readiness probe for the compatibility adapter.

The script reads the plugin config directly, never prints the Bot Token, and
does not advance Telegram's getUpdates cursor. Keep the adapter disabled while
running it so two getUpdates consumers do not conflict.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import tomllib
from typing import Any

import httpx


def load_config(path: pathlib.Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def response_description(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return ""
    return str(payload.get("description") or "")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe Telegram Bot API without printing secrets or consuming updates."
    )
    parser.add_argument(
        "--plugin-config",
        required=True,
        type=pathlib.Path,
        help="Path to exynos967_telegram-adapter/config.toml",
    )
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--update-limit", type=int, default=20)
    args = parser.parse_args()

    try:
        config = load_config(args.plugin_config)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        print(f"[FAIL] 无法读取插件配置: {type(exc).__name__}")
        return 2

    plugin = config.get("plugin") or {}
    telegram = config.get("telegram_bot") or {}
    enabled = bool(plugin.get("enabled"))
    token = str(telegram.get("token") or "").strip()
    api_base = str(telegram.get("api_base") or "https://api.telegram.org").rstrip("/")
    proxy_enabled = bool(telegram.get("proxy_enabled"))
    proxy_url = str(telegram.get("proxy_url") or "").strip()

    print(f"enabled={enabled}")
    print(f"token_present={bool(token)} token_length={len(token)}")
    print(f"proxy_enabled={proxy_enabled} proxy_configured={bool(proxy_url)}")

    if enabled:
        print("[FAIL] 适配器已启用。为避免两个 getUpdates 消费者冲突，请先关闭插件再运行探针。")
        return 2
    if not token:
        print("[FAIL] Token 为空。请把 BotFather Token 写入本机插件 config.toml 后重试。")
        return 2
    if proxy_enabled and not proxy_url:
        print("[FAIL] 已启用代理但 proxy_url 为空。")
        return 2

    proxy = proxy_url if proxy_enabled else None
    headers = {"User-Agent": "xuxingjiu-telegram-probe/1"}

    try:
        with httpx.Client(proxy=proxy, timeout=args.timeout, trust_env=False, headers=headers) as client:
            me_response = client.get(f"{api_base}/bot{token}/getMe")
            if me_response.status_code != 200:
                print(
                    f"[FAIL] getMe HTTP {me_response.status_code}: "
                    f"{response_description(me_response) or 'unknown error'}"
                )
                return 1
            me_payload = me_response.json()
            me = me_payload.get("result") or {}
            if not me_payload.get("ok") or not me.get("id"):
                print(f"[FAIL] getMe 响应异常: {response_description(me_response) or 'invalid payload'}")
                return 1

            bot_id = me["id"]
            username = str(me.get("username") or "")
            print(f"[OK] bot_id={bot_id} username={username or '(none)'}")

            updates_response = client.post(
                f"{api_base}/bot{token}/getUpdates",
                json={
                    "timeout": 0,
                    "limit": max(1, min(args.update_limit, 100)),
                    "allowed_updates": ["message"],
                },
            )
            if updates_response.status_code != 200:
                print(
                    f"[FAIL] getUpdates HTTP {updates_response.status_code}: "
                    f"{response_description(updates_response) or 'unknown error'}"
                )
                return 1
            updates_payload = updates_response.json()
            if not updates_payload.get("ok"):
                print(
                    f"[FAIL] getUpdates 响应异常: "
                    f"{response_description(updates_response) or 'invalid payload'}"
                )
                return 1
    except (httpx.HTTPError, ValueError) as exc:
        print(f"[FAIL] Telegram 连接失败: {type(exc).__name__}")
        print("       请检查代理是否处于连接状态，以及 api_base 是否可达。")
        return 1

    rows: list[tuple[str, str, str, str]] = []
    for update in updates_payload.get("result") or []:
        message = update.get("message") or {}
        chat = message.get("chat") or {}
        sender = message.get("from") or {}
        chat_id = chat.get("id")
        user_id = sender.get("id")
        if chat_id is None or user_id is None:
            continue
        chat_type = str(chat.get("type") or "")
        username = str(sender.get("username") or "")
        rows.append((chat_type, str(chat_id), str(user_id), username))

    print(f"pending_updates={len(rows)}")
    if not rows:
        print("暂无待处理消息。让维护者先给 Bot 发一条 /start，再运行一次。")
        return 0

    seen: set[tuple[str, str, str, str]] = set()
    for row in rows:
        if row in seen:
            continue
        seen.add(row)
        chat_type, chat_id, user_id, username = row
        print(
            f"chat_type={chat_type} chat_id={chat_id} "
            f"user_id={user_id} username={username or '(none)'}"
        )

    private_ids = sorted({row[2] for row in rows if row[0] == "private"})
    group_ids = sorted({row[1] for row in rows if row[0] in {"group", "supergroup"}})
    if private_ids:
        print("private_whitelist_candidates=" + json.dumps(private_ids, ensure_ascii=False))
    if group_ids:
        print("group_whitelist_candidates=" + json.dumps(group_ids, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
