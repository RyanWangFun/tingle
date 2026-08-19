#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发版前检查：机械事实一律由本程序判，不靠人记。

为什么有这个文件：同一批事实（版本号、装了哪些 skill、共几件）在四个地方各存
一份手写副本——市场清单、Claude 清单、Codex 清单（含 interface 那一块）、README。
真相其实只在 skills/ 目录里。手工同步四份，早晚漏一份；已经漏过一次：14 件新
skill 发出去时，两份清单的描述还停在"三个工作 skill"，Codex 那份的 longDescription
更是停在"现收录四个 skill"。

本程序只判机械事实（数得出来、比得了的），不判文案写得好不好——描述怎么写是人的活。

用法：
    python3 scripts/check-release.py          # 检查，有问题退出码 1
    python3 scripts/check-release.py --quiet   # 只在有问题时输出

推荐挂成 git pre-push 钩子，见本文件末尾说明。
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(ROOT, "plugins", "tingle", "skills")
README = os.path.join(ROOT, "README.md")
MANIFESTS = [
    os.path.join(ROOT, "plugins", "tingle", ".claude-plugin", "plugin.json"),
    os.path.join(ROOT, "plugins", "tingle", ".codex-plugin", "plugin.json"),
]
MARKETPLACE = os.path.join(ROOT, ".claude-plugin", "marketplace.json")

# 公开仓不许出现的东西：客户名、人名、本机绝对路径、内部文档路径
LEAK_PATTERNS = [
    r"町乐", r"琅玕", r"星罗", r"内舒拿", r"欣妈富隆", r"礼来", r"保法止",
    r"王玥冉", r"Penny",
    r"/Users/", r"/Volumes/", r"C:\\\\Users\\\\",
    r"01Projects", r"00-准绳", r"docs/praxis", r"conversation-summaries",
]

problems = []
notes = []


def fail(msg):
    problems.append(msg)


def note(msg):
    notes.append(msg)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


# ── 1. 收集真相：skills/ 目录 ────────────────────────────────────────────────
def collect_skills():
    skills = {}
    for d in sorted(os.listdir(SKILLS_DIR)):
        p = os.path.join(SKILLS_DIR, d)
        if not os.path.isdir(p):
            continue
        sk = os.path.join(p, "SKILL.md")
        if not os.path.exists(sk):
            fail(f"[结构] {d}/ 里没有 SKILL.md")
            continue
        text = read(sk)
        m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if not m:
            fail(f"[结构] {d}/SKILL.md 的 frontmatter 不合法")
            continue
        fm = m.group(1)
        nm = re.search(r"^name:\s*(\S+)", fm, re.M)
        if not nm:
            fail(f"[结构] {d}/SKILL.md 没有 name 字段")
            continue
        name = nm.group(1)
        if not re.fullmatch(r"[A-Za-z0-9-]+", name):
            fail(f"[命名] {d}/SKILL.md 的 name「{name}」含非法字符（只许字母数字连字符）")
        if name != d:
            fail(f"[命名] {d}/SKILL.md 的 name「{name}」与目录名不一致")
        if not re.search(r"^description:", fm, re.M):
            fail(f"[结构] {d}/SKILL.md 没有 description 字段")
        skills[d] = {"text": text, "dir": p}
    return skills


# ── 2. 引用完整性 ───────────────────────────────────────────────────────────
def check_references(skills):
    names = set(skills)
    for d, info in skills.items():
        files = [("SKILL.md", info["text"])]
        rdir = os.path.join(info["dir"], "references")
        if os.path.isdir(rdir):
            for rf in sorted(os.listdir(rdir)):
                if rf.endswith(".md"):
                    files.append((f"references/{rf}", read(os.path.join(rdir, rf))))

        for fname, text in files:
            # 跨技能引用：被引的技能必须存在
            for ref in re.findall(
                r"REQUIRED (?:SUB-SKILL|BACKGROUND): `tingle:([a-z-]+)`", text
            ):
                if ref not in names:
                    fail(f"[引用] {d}/{fname} 引了不存在的技能：{ref}")

            # 深读件路径：逐行判，且必须先看这一行有没有点名别的技能
            # （吃过一次亏：project-readiness 写的是「见 context-distill 参考件
            #   `references/x.md`」，只匹配路径会误报成本目录缺文件）
            for line in text.splitlines():
                owner_in_line = {n for n in names if n != d and n in line}
                for rf in re.findall(r"`references/([\w.-]+\.md)`", line):
                    if os.path.exists(os.path.join(info["dir"], "references", rf)):
                        continue
                    elsewhere = [
                        n for n in names
                        if os.path.exists(os.path.join(SKILLS_DIR, n, "references", rf))
                    ]
                    if owner_in_line and set(elsewhere) & owner_in_line:
                        note(
                            f"[跨技能路径] {d}/{fname} 指向 {elsewhere[0]} 的内部文件 {rf}"
                            f"——能用，但对方改目录就会断"
                        )
                    elif elsewhere:
                        fail(
                            f"[引用] {d}/{fname} 指向 references/{rf}，"
                            f"本目录没有，它实际在 {elsewhere}；句子里也没点名是谁的"
                        )
                    else:
                        fail(f"[引用] {d}/{fname} 指向的 references/{rf} 不存在")


# ── 3. 版本号三处一致 ───────────────────────────────────────────────────────
def check_versions():
    versions = {}
    for p in MANIFESTS:
        versions[os.path.relpath(p, ROOT)] = json.load(open(p, encoding="utf-8"))["version"]
    if len(set(versions.values())) > 1:
        fail(f"[版本] 各清单版本号不一致：{versions}")
    return next(iter(versions.values()))


# ── 4. 清单与 README 的件数说法要对得上实际 ────────────────────────────────
def check_counts(skills):
    n = len(skills)
    targets = [(p, read(p)) for p in MANIFESTS + [MARKETPLACE, README]]
    for p, text in targets:
        rel = os.path.relpath(p, ROOT)
        for m in re.finditer(r"(?:共\s*)?(\d+|[一二三四五六七八九十]+)\s*(?:个|件)\s*skill", text):
            raw = m.group(1)
            cn = {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10}
            val = int(raw) if raw.isdigit() else cn.get(raw)
            if val is None or val < 4:
                continue  # "一个 skill 管"这类行文，不是件数声明
            if val != n:
                fail(f"[件数] {rel} 写着「{m.group(0)}」，实际有 {n} 件")


# ── 5. README 的 skill 清单必须覆盖每一件 ──────────────────────────────────
def check_readme_listing(skills):
    text = read(README)
    m = re.search(r"^## 含哪些 skill\s*$(.*)", text, re.S | re.M)
    if not m:
        fail("[README] 找不到「## 含哪些 skill」这一节")
        return
    section = m.group(1)
    missing = [d for d in skills if d not in section]
    if missing:
        fail(f"[README] 清单里没有这几件：{missing}")
    # 反向：清单里点了名却不存在的
    for name in set(re.findall(r"\b([a-z][a-z-]{4,})\b", section)):
        if name in {"skill", "tingle", "claude", "readme"}:
            continue
        if re.search(rf"\*\*{re.escape(name)}", section) and name not in skills:
            fail(f"[README] 清单里点名的「{name}」在 skills/ 里不存在")


# ── 6. 公开仓泄漏扫描 ──────────────────────────────────────────────────────
def check_leaks():
    pat = re.compile("|".join(LEAK_PATTERNS))
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules"}]
        for fn in files:
            p = os.path.join(base, fn)
            rel = os.path.relpath(p, ROOT)
            if rel.startswith("scripts/check-release.py"):
                continue  # 本文件自带模式串
            try:
                text = read(p)
            except (UnicodeDecodeError, IsADirectoryError, PermissionError):
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if pat.search(line):
                    fail(f"[泄漏] {rel}:{i} 命中不该进公开仓的内容：{line.strip()[:80]}")


def main():
    quiet = "--quiet" in sys.argv
    skills = collect_skills()
    check_references(skills)
    version = check_versions()
    check_counts(skills)
    check_readme_listing(skills)
    check_leaks()

    if problems:
        print(f"\n✗ 发版检查未通过（{len(problems)} 项）\n")
        for p in problems:
            print(f"  {p}")
        if notes:
            print("\n  另有提示（不拦发版）：")
            for n in notes:
                print(f"    {n}")
        print()
        return 1

    if not quiet:
        print(f"✓ 发版检查通过：版本 {version}，{len(skills)} 件 skill，"
              f"清单与 README 对得上，无泄漏")
        for n in notes:
            print(f"  提示：{n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# ── 挂成 git 钩子（一次性设置，每台开发机各做一次）──────────────────────────
#   git config core.hooksPath .githooks
# 之后每次 git push 前自动跑本检查，不通过就拦下。
