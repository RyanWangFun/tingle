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

## 含哪些 skill

- **on-trend-radar（选题雷达）**：把当天的热点/热搜接到某个项目的目标人群与痛点上，判断哪条热点值得立成一条选题，产出待复核的选题清单。

本插件是一个会长大的容器，后续会持续加入更多跨项目复用的 skill；新增 skill 不改变插件名称与安装方式。
