# Tingle

Tingle 是 Ryan 的可复用工作 skill 合集，以 Claude Code 插件的形式打包，方便同事一次安装、持续使用。它是一个会长大的容器：插件名称固定为 `tingle`，往后新增的 skill 都会归入同一个插件，无需重新安装或更改安装命令。

## 前置依赖 / Requirements

使用本插件内的 skill 前，请先确认以下依赖已就绪：

- 已安装 `lark-cli`（`larksuite/cli`）
- 已执行 `npx skills add larksuite/cli -g` 完成安装
- 已执行 `lark-cli auth login` 完成飞书授权
- 拥有相关飞书表的访问权：当天热点榜表、各项目自己的「项目选题上下文」云文档、选题清单表

## 安装

```
/plugin marketplace add https://github.com/RyanWangFun/tingle
/plugin install tingle@tingle
```

## 含哪些 skill

- **on-trend-radar（选题雷达）**：把当天的热点/热搜接到某个项目的目标人群与痛点上，判断哪条热点值得立成一条选题，产出待复核的选题清单。

本插件是一个会长大的容器，后续会持续加入更多跨项目复用的 skill；新增 skill 不改变插件名称与安装方式。
