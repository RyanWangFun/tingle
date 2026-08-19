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


# ── 6. 生产端与消费端的契约对得上 ──────────────────────────────────────────
#   起因：把「品牌项目红线」从归集件改成判据件（每条要带「该怎么改」）之后，
#   11 个消费者的就绪判据仍是照旧形态写的，没有一条要改法——一份旧形状的件
#   能通过全部 11 道闸，那次升级在下游零效果，而且无处报错。
#   根因与「同一批事实四处各存一份手写副本」同类，只是换了层级：一份契约
#   的两端各写各的，改一端另一端不会响。故交程序判。
def check_input_contract(skills):
    manifest_owner = "project-readiness"
    if manifest_owner not in skills:
        return
    text = skills[manifest_owner]["text"]
    m = re.search(r"<!-- DISTILL-MANIFEST BEGIN -->(.*?)<!-- DISTILL-MANIFEST END -->",
                  text, re.S)
    if not m:
        fail(f"[契约] {manifest_owner} 里找不到认知件清单块（DISTILL-MANIFEST 标记）")
        return
    block = m.group(1)

    # 6.1 清单块必须是合法 YAML——这块栽过两次（值以 * 开头被当锚点；一个键
    #     既给值又挂下级键）。坏了不报错，只是下游读它的模型自己猜。
    ym = re.search(r"```yaml\n(.*?)\n```", block, re.S)
    if not ym:
        fail("[契约] 认知件清单块里没有 yaml 代码块")
        return
    try:
        import yaml
        try:
            yaml.safe_load(ym.group(1))
        except Exception as e:
            first = str(e).strip().splitlines()[0]
            fail(f"[契约] 认知件清单块不是合法 YAML：{first}")
    except ImportError:
        note("[契约] 未装 PyYAML，跳过清单块的 YAML 合法性检查（pip install pyyaml 可开启）")

    # 6.1b 每个用到的形态，形态定义里要有条目、产不产段里要有判法。
    #      起因：清单加了「提炼件」这一形态，但「产不产」段没跟着分叉，于是那一段
    #      仍只有「对着 raw/ 问，全无则不产」一套判法——而提炼件不另收料，拿它去问
    #      永远答「全无」，结果是每个项目都把它静默判成「本项目无料·未产」。
    #      比停机更难发现：不产、不算缺、不催，没人会知道。
    try:
        import yaml as _y
        _d = _y.safe_load(ym.group(1))
        used = {it.get("形态") for it in (_d.get("认知件套") or []) if it.get("形态")}
        defined = set((_d.get("形态定义") or {}).keys())
        for f in sorted(used - defined):
            fail(f"[契约] 清单里有件用了形态「{f}」，但「形态定义」段里没有它的条目")
        pnp = _d.get("产不产") or {}
        judged = set()
        for k, v in pnp.items():
            if isinstance(v, dict):
                ap = v.get("适用形态")
                if ap:
                    judged |= {x.strip() for x in re.split(r"[／/、]", ap) if x.strip()}
                elif k in used:
                    judged.add(k)
        for f in sorted(used - judged):
            fail(f"[契约] 清单里有件用了形态「{f}」，但「产不产」段里没有对它的判法——"
                 f"缺判法不会报错，只会被另一支的判法误判，且误判是静默的")
    except ImportError:
        pass
    except Exception as e:
        note(f"[契约] 形态覆盖检查跳过（清单块解析异常：{str(e).splitlines()[0][:60]}）")

    # 6.2 件名 → 形态
    forms = dict(re.findall(r"- 件名:\s*(\S+)\s*\n\s*形态:\s*(\S+)", block))
    if not forms:
        fail("[契约] 认知件清单块里解析不出任何「件名 / 形态」")
        return

    # 6.3 消费端：produced_by 为 context-distill 的每一处声明
    for d, sk in sorted(skills.items()):
        for dm in re.finditer(
                r'"([^"]+)":\s*\{[^{}]*?"就绪判据":\s*\[(.*?)\][^{}]*?"produced_by":\s*"context-distill"',
                sk["text"], re.S):
            item, crit = dm.group(1), dm.group(2)
            form = forms.get(item)
            if form is None:
                # 不在清单里 = 第四意图的 skill 专用输入件，另有一套，不在本检查范围
                continue
            if form == "判据件" and "改法" not in crit:
                fail(f"[契约] {d} 向「{item}」要的就绪判据里没有「改法」——"
                     f"该件形态是判据件（每条须带『该怎么改』），"
                     f"判据不要它，等于用旧形态的尺子量新形态的件")


def main():
    quiet = "--quiet" in sys.argv
    skills = collect_skills()
    check_references(skills)
    version = check_versions()
    check_counts(skills)
    check_readme_listing(skills)
    check_leaks()
    check_input_contract(skills)

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
