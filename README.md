# Tingle

Tingle 是 Ryan 的可复用工作 skill 合集，以 Claude Code 插件的形式打包，方便同事一次安装、持续使用。它是一个会长大的容器：插件名称固定为 `tingle`，往后新增的 skill 都会归入同一个插件，无需重新安装或更改安装命令。

## 前置依赖 / Requirements

**先配好前置依赖，再装插件。** 本插件内的 skill 依赖 lark 工具链读写飞书：

- 安装 `lark-cli`（`larksuite/cli`）：在系统终端跑 `npx skills add larksuite/cli -g`
- 执行 `lark-cli auth login` 完成飞书授权
- 拥有相关飞书表的访问权：当天热点榜表、各项目自己的「项目选题上下文」云文档、选题清单表

## 安装

> 说明：`/plugin …` 是在 **Claude Code 对话框里**输入的斜杠命令（不是系统终端）；`$skill-installer`、`npx` 是在**系统终端**里跑。

### Claude Code

在 Claude Code 会话里依次输入：

```
/plugin marketplace add RyanWangFun/tingle
/plugin install tingle@tingle
/reload-plugins
```

装好后即可使用。选题雷达是 model-invoked 技能，Claude 会按任务自动调用（如需显式调用，名为 `/tingle:on-trend-radar`）。

### Codex

Codex 支持从 GitHub 加载**插件市场**。在 Codex 的「插件 → 添加插件市场」对话框里填：

- 来源：`RyanWangFun/tingle`
- Git 引用：`main`（主分支）
- 稀疏路径：留空

或用命令行：

```
codex plugin marketplace add RyanWangFun/tingle
```

添加市场后，在插件列表里安装 `tingle`。新装插件 Codex 会自动发现，没出现就重启 Codex。

## 双侧差异（Claude Code vs Codex）

tingle 的会话入口（using-tingle）经 SessionStart hook 随会话自动注入，在 Claude Code 与 Codex 两侧同构生效——同一份 hook 文件双侧通用，无需分别配置。需要知道的差异只有两点：

1. **信任门槛**：Codex 安装或启用插件后，插件自带的 hooks 不会自动生效——按 Codex 官方文档的说明，插件捆绑的 hooks 属于非托管 hooks，需要用户在 Codex 中审核并信任本插件的 hook 定义后才会运行（Claude Code 无此额外步骤）。在信任生效前，可在对话里直接说「使用 using-tingle」手动加载入口。
2. **输出上限**：按 Codex 官方文档的说明，Codex 侧 hook 对模型可见的注入内容有约 2,500 token 的上限，超出部分会被截断。当前入口注入内容的实测长度随 tokenizer 口径而异：按 `o200k_base` 计为 2004 token（距上限约 496），按 `cl100k_base` 计为 2511 token（超出约 11）。Codex 实际按哪种口径计数尚未在真机上实测，故不排除注入尾部被截去十余 token 的可能；若发现入口内容不完整，在对话里直接说「使用 using-tingle」手动加载即可。改动入口内容时，请按上述两种口径各复算一次，不要在现有长度上继续加长。

## 含哪些 skill

- **using-tingle（会话入口）**：每次会话开始时自动加载（无需你调用），确认当前在哪个项目里工作、该项目是否已就绪；未就绪则引导你走初始化，不让 skill 在缺前提的情况下空跑。
- **project-readiness（项目就绪）**：本插件的就绪总管。① 各 skill 运行前由它检查这一次的前提齐不齐（缺则说明卡在哪、不让这次跑）；② 也可以直接对它说「把这个项目弄就绪」，它会带你把一个新项目从零配齐——建云盘落点、收料、蒸上下文、打标签、建承接表、写项目档案。凡要写飞书的动作都会先停下来等你放行。
- **context-distill（项目上下文蒸馏）**：把散在各处的项目材料收拢上飞书云盘，蒸馏成全家族共用的项目上下文；材料更新后就地重蒸，不推倒重来。
- **on-trend-radar（选题雷达）**：把当天的热点/热搜接到某个项目的目标人群与痛点上，判断哪条热点值得立成一条选题，产出待复核的选题清单。

本插件是一个会长大的容器，后续会持续加入更多跨项目复用的 skill；新增 skill 不改变插件名称与安装方式。
