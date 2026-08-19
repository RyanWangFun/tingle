# 维护这个仓

面向改这个插件的人（含 AI 会话）。装插件用的说明在 `README.md`。

## 发版前跑一次检查

```
python3 scripts/check-release.py
```

**为什么有它**：同一批事实在四个地方各存一份手写副本——

| 地方 | 存了什么 |
|---|---|
| `.claude-plugin/marketplace.json` | 描述 |
| `plugins/tingle/.claude-plugin/plugin.json` | 版本号、描述 |
| `plugins/tingle/.codex-plugin/plugin.json` | 版本号、描述，**外加 `interface` 那一块**（`shortDescription` / `longDescription` / `defaultPrompt`，只有 Codex 侧有） |
| `README.md` | 发版说明、skill 清单 |

而真相只在 `plugins/tingle/skills/` 里。**手工同步四份，早晚漏一份**——已经漏过：14 件新 skill 发出去时，两份清单的描述还停在「三个工作 skill」，Codex 那份的 `longDescription` 更是停在「现收录四个 skill」。

所以机械事实（数得出来、比得了的）一律交给程序判：版本号三处一致、件数说法对得上实际、README 清单覆盖每一件、skill 的 name 与目录名一致、跨技能引用指向真实存在的技能、深读件路径找得到、公开仓无泄漏。

**它不判文案写得好不好**——描述怎么写是人的活，程序不碰。

## 让它不依赖谁记得跑

```
git config core.hooksPath .githooks
```

**每台开发机做一次。** 之后每次 `git push` 前自动跑，不通过就拦下（确需绕过用 `git push --no-verify`）。

## 加了新 skill 之后要动的地方

1. skill 目录进 `plugins/tingle/skills/`（目录名 = `SKILL.md` 里的 `name`，只许字母数字连字符）
2. 三份清单的描述里，把它算进件数与分类
3. `README.md` 的「含哪些 skill」补一条；有必要就加一节发版说明
4. **`.codex-plugin/plugin.json` 的 `interface.longDescription` 单独改一遍**——它跟顶层 `description` 是两份，最容易漏的就是它
5. 跑一次检查器

## 版本号怎么定

- 新增 skill、新增能力 → 次版本号（`0.8.x` → `0.9.0`）
- 改文案、修 bug、不动能力面 → 修订号
- 常驻件或状态文件的**结构版本**变了 → 在发版说明里写清「升级后每个项目跑一次 `tingle resolve`」，那是使用者要动手的事

## 加检查项

检查器发现漏判时，回 `scripts/check-release.py` 补一条，**并造一份故意坏的样例撞一次**——没被判红过的检查项，跟没有它是一样的。
