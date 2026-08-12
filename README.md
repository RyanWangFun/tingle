# Tingle

Tingle 是 Ryan 的可复用工作 skill 合集，以 Claude Code 插件的形式打包，方便同事一次安装、持续使用。它是一个会长大的容器：插件名称固定为 `tingle`，往后新增的 skill 都会归入同一个插件，无需重新安装或更改安装命令。

## 前置依赖 / Requirements

**先配好前置依赖，再装插件。** 本插件内的 skill 依赖 lark 工具链读写飞书：

- 安装 `lark-cli`（`larksuite/cli`）：在系统终端跑 `npx skills add larksuite/cli -g`——这一步同时把 `lark-*` 系列 skill（`lark-doc` / `lark-base` / `lark-drive` 等）装到位，插件内的 skill 全靠它们读写飞书，缺了就跑不动
- 执行 `lark-cli auth login` 完成飞书授权，并保持授权有效（授权走你本人的飞书身份，过期了重跑一次）
- 拥有该项目飞书云盘文件夹的访问权——材料、蒸出来的项目上下文、项目档案、项目总索引都落在那里

## 安装

> 说明：`/plugin …` 是在 **Claude Code 对话框里**输入的斜杠命令（不是系统终端）；`npx` 是在**系统终端**里跑。

### Claude Code

在 Claude Code 会话里依次输入：

```
/plugin marketplace add RyanWangFun/tingle
/plugin install tingle@tingle
/reload-plugins
```

装好后即可使用。会话入口随会话自动加载，其余 skill 都是 model-invoked 技能，Claude 会按任务自动调用（如需显式调用，名为 `/tingle:<skill 名>`，如 `/tingle:project-readiness`）。

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

tingle 的会话入口（using-tingle）经 SessionStart hook 随会话自动注入，两侧共用同一份 hook 文件，无需分别配置。Claude Code 装完即用；Codex 多两步，都只做一次。

**第一步：信任本插件的 hook。** Codex 装好或启用插件后，插件自带的 hook 不会立刻生效——按 Codex 官方文档，插件捆绑的 hook 属于非托管 hook，须由你审核并信任后才运行（Claude Code 无此步骤）。在 Codex 里用 `/hooks` 查看并信任即可。

要点：**信任是按 hook 定义的内容记录的**，所以插件更新一旦改动了 hook 定义，它会重新变回待审核状态、hook 被跳过，届时再用 `/hooks` 信任一次即可（0.4.1 就改动了 hook 定义，从更早版本升上来的话请重新信任）。信任生效前，在对话里直接说「使用 using-tingle」可手动加载入口。

**第二步（仅当 `/hooks` 里根本看不到本插件的 hook 时）：手动登记一次。** 看不到说明你这个 Codex 版本尚未开启"自动发现插件自带 hook"的能力（该能力在 Codex 中曾置于特性开关之后）。这时把下面这段加进 `~/.codex/hooks.json`，效果完全相同——本插件的 hook 脚本会自行推导插件位置、不依赖任何环境变量，所以按绝对路径调用照样工作：

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear|compact",
        "hooks": [
          {
            "type": "command",
            "command": "'<插件安装路径>/hooks/session-start.sh'",
            "timeout": 10,
            "additionalContextLimit": 0
          }
        ]
      }
    ]
  }
}
```

`<插件安装路径>` 换成本插件在你机器上的实际位置。不确定装在哪，在终端跑这条即可查出脚本的完整路径，直接把它填进去：

```bash
find ~/.codex -name session-start.sh -path '*tingle*' 2>/dev/null
```

加完同样需要用 `/hooks` 信任一次。

**关于注入长度**：Codex 对 hook 注入内容默认有约 2,500 token 的上限，超出部分不会被截断，而是被存进临时文件、只给模型一段头尾预览加文件路径——对入口来说这比截断更糟，模型多半不会去读那个文件。本插件的 hook 已声明 `additionalContextLimit: 0`（完整内容原样交给模型），所以入口全文总是完整到场，改动入口内容时也无需再核算长度。**这个字段不要删。**

## 含哪些 skill

- **using-tingle（会话入口）**：每次会话开始时自动加载（无需你调用），确认当前在哪个项目里工作、这个项目在你机器上初始化过没有；没初始化过就把你带到初始化那一步。它管到这里为止——之后每次干活前的前提检查不归它，归下面的 project-readiness。
- **project-readiness（项目就绪）**：本插件的就绪总管。① 各 skill 运行前由它检查这一次的前提齐不齐（缺则说明卡在哪、不让这次跑）；② 也可以直接对它说「把这个项目弄就绪」，它会带你把一个新项目从零配齐——建云盘落点、打标签、标明项目走到哪个阶段、收料、把材料整理成 AI 读得了的形态、蒸出项目上下文，最后写项目档案和一份项目总索引（这个项目有哪几类东西、每类从哪儿进）。凡要写飞书的动作都会先停下来等你放行。
- **context-distill（项目上下文蒸馏）**：把散在各处的项目材料收拢上飞书云盘，蒸馏成全家族共用的项目上下文；材料更新后就地重蒸，不推倒重来。

这三件合起来是一套**项目初始化基础设施**——把一个客户项目在你自己机器上从零弄到能干活。初始化完成的标准是「地基齐」（云盘落点、材料、项目上下文、项目档案、项目总索引、本地锚），不以任何具体业务技能就绪为准。

- **building-work-skill（把做法造成 skill）**（0.5.0 新增）：你手上有一套已经在用的做法——可能是口述的、一份工作流走查纪要，或者一个自己攒的自用件——它带你把这套做法变成别人也能装上就用的 skill。逐道过五关：这个 skill 到底管哪一段（别一个 skill 塞两件事）、哪些规则该外置到哪一层（别把某个客户的规矩焊死在正文里）、用到的每样东西从哪儿来（别留下"运行时自然就有"的悬空）、哪几步不许自动、得停下来让人判、以及怎么测它。

  它跟上面三件的关系：那三件负责**把项目弄到能干活**，这一件负责**把你的做法变成能复用的工具**。两边独立，不必按顺序用。

本插件是一个会长大的容器，后续会持续加入更多跨项目复用的 skill；新增 skill 不改变插件名称与安装方式。
