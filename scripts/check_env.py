# -*- coding: utf-8 -*-
"""许杏玖（MaiBot 版）环境体检。

用法：
    python check_env.py                 # 只检查
    python check_env.py --maibot <路径>  # 指定 MaiBot 根目录

检查项：
  1. 关键端口是否在监听（控制端 / MaiBot / TTS / ComfyUI）
  2. MaiBot 的插件加载情况（有没有加载失败）
  3. 配置模板里的凭据是不是真的还空着（防止把实盘配置误发出去）
  4. 内存余量（ComfyUI 吃内存，提交不够会起不来）

只读，不改任何东西。
"""
from __future__ import annotations
import argparse
import json
import pathlib
import re
import socket
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PORTS = [
    (3000, "OneBot HTTP（SnowLuma / NapCat）"),
    (3001, "OneBot WS（SnowLuma / NapCat）"),
    (8000, "MaiBot 主服务"),
    (8001, "MaiBot WebUI"),
    (9880, "GPT-SoVITS api_v2"),
    (8188, "ComfyUI（画图后端，可选）"),
    (11434, "Ollama（本地 embedding，16G 机器建议改云端）"),
]
SECRET_RX = re.compile(
    r'(api_key|token|p_skey|skey|secret|password)\s*=\s*"([^"]+)"', re.I)
QQID_RX = re.compile(r"\b(?:1[3-9]\d{8,9}|2\d{8,9})\b")
PLACEHOLDER_RX = re.compile(r"<[^>]{1,40}>")

ok = True


def check_port(port, label):
    global ok
    s = socket.socket()
    s.settimeout(1.5)
    try:
        alive = s.connect_ex(("127.0.0.1", port)) == 0
    finally:
        s.close()
    mark = "OK  " if alive else "空闲"
    if not alive and port in (3000, 3001, 8000, 8001):
        ok = False
    print(f"  [{mark}] {port:<6} {label}")
    return alive


def check_plugins(mb: pathlib.Path):
    global ok
    logdir = mb / "logs"
    if not logdir.exists():
        print("  [跳过] 没有 logs 目录")
        return
    files = sorted(logdir.glob("app_*.log.jsonl"), key=lambda p: p.stat().st_mtime,
                   reverse=True)[:2]
    if not files:
        print("  [跳过] 没有日志文件")
        return
    fails = []
    loaded = 0
    for p in files:
        for line in p.open(encoding="utf-8", errors="replace"):
            if "插件注册失败" in line or "Manifest 校验失败" in line:
                fails.append(line[:160])
            if "已加载=" in line:
                m = re.search(r"已加载=(\d+)", line)
                if m:
                    loaded = max(loaded, int(m.group(1)))
    print(f"  [INFO] 最近日志里报告已加载插件数: {loaded or '未知'}")
    if fails:
        ok = False
        print(f"  [FAIL] 发现 {len(fails)} 条插件加载失败：")
        for f in fails[:5]:
            print("      ", f)
    else:
        print("  [OK  ] 没有插件加载失败")


def check_templates(repo: pathlib.Path):
    global ok
    cfgdir = repo / "config"
    if not cfgdir.exists():
        print("  [跳过] 没有 config 目录")
        return
    for f in sorted(cfgdir.glob("*.example.toml")):
        t = f.read_text(encoding="utf-8", errors="replace")
        filled = [(m.group(1), m.group(2)[:8] + "...") for m in SECRET_RX.finditer(t)
                  if m.group(2) and not PLACEHOLDER_RX.match(m.group(2))]
        ids = sorted(set(QQID_RX.findall(t)))
        if filled or ids:
            ok = False
            print(f"  [FAIL] {f.name} 里有不该出现的东西：")
            for k, v in filled[:5]:
                print(f"        {k} = {v}")
            if ids:
                print(f"        疑似真实 QQ 号: {ids[:5]}")
        else:
            print(f"  [OK  ] {f.name} 干净（凭据全空、无真实 QQ 号）")


def check_memory():
    global ok
    try:
        import psutil  # type: ignore
        vm = psutil.virtual_memory()
        print(f"  [INFO] 物理可用 {vm.available/1e9:.1f} GB / 总 {vm.total/1e9:.1f} GB")
        if vm.available < 1.5e9:
            ok = False
            print("       ⚠ 可用内存 < 1.5 GB，ComfyUI 这类重服务会起不来")
    except Exception:
        print("  [跳过] 没装 psutil")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--maibot", default="MaiBot",
                    help="MaiBot 根目录（默认按相对路径 ./MaiBot 找）")
    ap.add_argument("--repo", default=str(pathlib.Path(__file__).resolve().parent.parent),
                    help="本仓库根目录（用来找 config 模板）")
    args = ap.parse_args()

    print("=== 1. 端口 ===")
    for p, label in PORTS:
        check_port(p, label)

    print("\n=== 2. 插件加载 ===")
    check_plugins(pathlib.Path(args.maibot))

    print("\n=== 3. 配置模板是否干净 ===")
    check_templates(pathlib.Path(args.repo))

    print("\n=== 4. 内存余量 ===")
    check_memory()

    print("\n" + ("全部通过" if ok else "有需要处理的项目（见上面标 FAIL 的）"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
