<h1 align="center">Sift</h1>

<p align="center">
面向 Mihomo 的无节点分流模板 — 只提供策略组、远程规则和分流顺序，不内置节点与 DNS。
</p>

<p align="center">
  <img alt="Mihomo" src="https://img.shields.io/badge/Mihomo-compatible-blue">
  <img alt="Rules" src="https://img.shields.io/badge/rules-MRS-green">
  <img alt="Node Free" src="https://img.shields.io/badge/nodes-not%20included-lightgrey">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-blue">
</p>

## 模板

| 文件 | 策略组 | 规则提供商 | 说明 |
| --- | ---: | ---: | --- |
| [`Full.yaml`](./Full.yaml) | 17 | 16 | 完整版：AI、娱乐、Google/Apple/Microsoft、开发工具、游戏平台、地区节点 |
| [`Mini.yaml`](./Mini.yaml) | 5 | 11 | 极简版：AI、娱乐内容、兜底，适合轻量环境 |

```text
https://raw.githubusercontent.com/WillLiang713/Sift/main/Full.yaml
https://raw.githubusercontent.com/WillLiang713/Sift/main/Mini.yaml
```

## 设计要点

- **无节点**：模板不含 `proxies`，节点由订阅合并或本地配置补充。
- **不接管 DNS**：不写顶层 `dns` / `fake-ip`，留给客户端本地管理。
- **兜底出口**：未命中规则进入 `漏网之鱼`，避免未知流量被静默直连。
- **游戏独立**：国内游戏直连，境外游戏经 `游戏平台` 策略组（Full），避免被兜底代理误伤。

## 分流顺序

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | 国内 Google / Apple / Microsoft / 游戏 | `DIRECT` |
| 3 | AI 服务 | `AI` |
| 4 | 游戏平台（仅 Full） | `游戏平台` |
| 5 | 娱乐内容 | `娱乐内容` |
| 6 | 开发工具（仅 Full） | `开发工具` |
| 7 | Google / Apple / Microsoft 服务（仅 Full） | `谷歌服务` / `苹果服务` / `微软服务` |
| 8 | GFW 代理规则 | `节点选择` |
| 9 | 国内域名 / IP 兜底 | `DIRECT` |
| 10 | 未命中流量 | `漏网之鱼` |

## 策略组

**通用**：`节点选择` · `自动测速` · `AI` · `娱乐内容` · `漏网之鱼`

**Full 额外**：`谷歌服务` · `苹果服务` · `微软服务` · `开发工具` · `游戏平台` · `香港节点` · `美国节点` · `日本节点` · `新加坡节点` · `其他节点`

> 地区组依赖节点名称中的地区关键词自动归类。建议节点命名包含 `HK`、`日本`、`US` 等标识。

## 规则来源

使用远程 MRS 规则集，不提交规则文件：

- [DustinWin MRS](https://github.com/DustinWin/ruleset_geodata)：私有地址、国内服务、国内域名/IP、AI、游戏、GFW
- [MetaCubeX MRS](https://github.com/MetaCubeX/meta-rules-dat)：娱乐内容、开发工具、Google、Apple、Microsoft
- [Koolson/Qure](https://github.com/Koolson/Qure)、[Orz-3/mini](https://github.com/Orz-3/mini)：策略组图标

## 使用

1. 复制模板的 Raw 链接，在 Mihomo 客户端中作为远程模板引用。
2. 与节点订阅合并，或手动补充 `proxies`。
3. 也可直接 clone 后按需编辑：

```bash
git clone https://github.com/WillLiang713/Sift.git
```


## 兼容性要求

客户端需支持：Mihomo 核心、`rule-providers`、`RULE-SET`、`format: mrs`、策略组 `include-all` 与 `filter` 关键词匹配。

## 目录结构

```text
├── Full.yaml          # 完整模板
├── Mini.yaml          # 极简模板
├── AGENTS.md          # 维护约定
└── LICENSE
```

## License

[MIT](./LICENSE) · 远程规则与图标属于各自上游项目，使用前请遵守其许可条款。
