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
| [`Full.yaml`](./Full.yaml) | 13 | 11 | 完整版：AI、娱乐、游戏平台、地区节点 |
| [`Nano.yaml`](./Nano.yaml) | 6 | 4 | 极简版：直连/代理/兜底，最轻量的日常分流 |

```text
https://raw.githubusercontent.com/WillLiang713/Sift/main/Full.yaml
https://raw.githubusercontent.com/WillLiang713/Sift/main/Nano.yaml
```

## 设计要点

- **无节点**：模板不含 `proxies`，节点由订阅合并或本地配置补充。
- **不接管 DNS**：不写顶层 `dns` / `fake-ip`，留给客户端本地管理。
- **双层节点选择**：`节点选择` 作为日常总控入口，`手动切换` 才展开全部节点，节点多时面板更清爽。
- **可切换直连**：国内服务与国内兜底默认进入 `全球直连`，保持直连优先，同时允许临时切到总控或自动策略排障。
- **兜底出口**：未命中规则进入 `漏网之鱼`，避免未知流量被静默直连。
- **游戏独立**：国内游戏直连，境外游戏经 `游戏平台` 策略组，避免被兜底代理误伤。
- **国外流量**：代理规则命中流量统一进入 `国外流量`，可按需切换节点或地区。

## 分流顺序

### Full

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | 国内 Google / Apple / Microsoft / 游戏 | `全球直连` |
| 3 | AI 服务 | `AI` |
| 4 | 游戏平台 | `游戏平台` |
| 5 | 娱乐内容 | `娱乐内容` |
| 6 | 代理规则命中 | `国外流量` |
| 7 | 国内域名 / IP 兜底 | `全球直连` |
| 8 | 未命中流量 | `漏网之鱼` |

### Nano

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | 代理规则命中 | `国外流量` |
| 3 | 国内域名 / IP 兜底 | `全球直连` |
| 4 | 未命中流量 | `漏网之鱼` |

## 策略组

**Full**：`节点选择` · `手动切换` · `自动测速` · `全球直连` · `国外流量` · `AI` · `娱乐内容` · `游戏平台` · `漏网之鱼` · `香港节点` · `美国节点` · `日本节点` · `新加坡节点` · `其他节点`

**Nano**：`节点选择` · `手动切换` · `自动测速` · `全球直连` · `国外流量` · `漏网之鱼`

> 地区组依赖节点名称中的地区关键词自动归类。建议节点命名包含 `HK`、`日本`、`US` 等标识。

## 规则来源

远程 MRS 规则集全部由 [DustinWin/ruleset_geodata](https://github.com/DustinWin/ruleset_geodata) 提供：

- **Full**：`private` · `privateip` · `google-cn` · `apple-cn` · `microsoft-cn` · `games-cn` · `ai` · `media` · `games` · `proxy` · `cn`
- **Nano**：`private` · `privateip` · `proxy` · `cn`
- [Koolson/Qure](https://github.com/Koolson/Qure)、[Orz-3/mini](https://github.com/Orz-3/mini)：策略组图标

## 使用

1. 复制模板的 Raw 链接，在 Mihomo 客户端中作为远程模板引用。
2. 与节点订阅合并，或手动补充 `proxies`。
3. 也可直接 clone 后按需编辑：

```bash
git clone https://github.com/WillLiang713/Sift.git
```


## 兼容性要求

客户端需支持：Mihomo 核心、`rule-providers`、`RULE-SET`、`GEOIP`、`format: mrs`、策略组 `include-all` 与 `filter` 关键词匹配。

## 目录结构

```text
├── Full.yaml          # 完整模板
├── Nano.yaml          # 极简模板
├── AGENTS.md          # 维护约定
├── ruleset/           # 远程规则缓存（DustinWin）
└── LICENSE
```

## License

[MIT](./LICENSE) · 远程规则与图标属于各自上游项目，使用前请遵守其许可条款。
