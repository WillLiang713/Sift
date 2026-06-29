<h1 align="center">Sift</h1>

<p align="center">
面向通用代理内核的无节点分流模板 — 只提供策略组、远程规则和分流顺序，不内置节点。
</p>

<p align="center">
  <img alt="Core" src="https://img.shields.io/badge/core-compatible-blue">
  <img alt="Rules" src="https://img.shields.io/badge/rules-MRS-green">
  <img alt="Node Free" src="https://img.shields.io/badge/nodes-not%20included-lightgrey">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-blue">
</p>

## 模板

| 文件 | 策略组 | 规则提供商 | 说明 |
| --- | ---: | ---: | --- |
| [`Full.yaml`](./Full.yaml) | 16 | 17 | 完整版：AI、流媒体、游戏平台、苹果、微软、OneDrive、Telegram IP、地区节点；内置 fake-ip 分流 DNS |
| [`Nano.yaml`](./Nano.yaml) | 5 | 5 | 极简版：局域网直连、GFW 代理、国内直连和兜底分流 |

```text
https://raw.githubusercontent.com/WillLiang713/Sift/main/Full.yaml
https://raw.githubusercontent.com/WillLiang713/Sift/main/Nano.yaml
```

## 设计要点

- **无节点**：模板不含 `proxies`，节点由订阅合并或本地配置补充。
- **DNS 分模板**：Nano 不接管 DNS，留给客户端本地管理；Full 内置 fake-ip 分流 DNS（国内直连规则集、BT/STUN/游戏回流返回真实 IP，默认解析走海外 DoH，国内直连规则集和代理节点解析走国内 DoH），OpenClash 等客户端接管 DNS 时以客户端为准。
- **双层节点选择**：`节点选择` 作为日常总控入口，`手动切换` 才展开全部节点，节点多时面板更清爽。
- **可切换直连**：国内服务与国内兜底默认进入 `全球直连`，保持直连优先，同时允许临时切到总控或自动策略排障。
- **兜底出口**：未命中规则进入 `漏网之鱼`，避免未知流量被静默直连。
- **游戏独立**：国内游戏直连，境外游戏经 `游戏平台` 策略组，避免被兜底代理误伤。
- **聚合入口**：代理规则命中流量统一进入 `节点选择`，不再单独占用一个策略组。

## 分流顺序

### Full

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | 国内 Google / Apple / Microsoft / 游戏 | `全球直连` |
| 3 | Apple 海外服务 | `苹果服务` |
| 4 | AI 服务 | `AI` |
| 5 | 游戏平台 | `游戏平台` |
| 6 | 流媒体 | `流媒体` |
| 7 | OneDrive 网盘 | `OneDrive` |
| 8 | Microsoft 海外服务 | `微软服务` |
| 9 | 国外域名代理规则命中 | `节点选择` |
| 10 | Telegram IP | `节点选择` |
| 11 | 国内域名 / IP 兜底 | `全球直连` |
| 12 | 未命中流量 | `漏网之鱼` |

### Nano

| 优先级 | 规则 | 出口 |
| --- | --- | --- |
| 1 | 局域网 / 私有地址 | `DIRECT` |
| 2 | GFW 代理规则命中 | `节点选择` |
| 3 | 国内域名 / IP 兜底 | `全球直连` |
| 4 | 未命中流量 | `漏网之鱼` |

## 策略组

**Full**：`节点选择` · `手动切换` · `自动测速` · `全球直连` · `AI` · `流媒体` · `游戏平台` · `苹果服务` · `微软服务` · `OneDrive` · `漏网之鱼` · `香港节点` · `美国节点` · `日本节点` · `新加坡节点` · `其他节点`

**Nano**：`节点选择` · `手动切换` · `自动测速` · `全球直连` · `漏网之鱼`

> 地区组依赖节点名称中的地区关键词自动归类。建议节点命名包含 `HK`、`日本`、`US` 等标识。

## 规则来源

远程规则集主要由 [DustinWin/ruleset_geodata](https://github.com/DustinWin/ruleset_geodata) 提供（MRS）；海外 Apple / Microsoft / OneDrive 取自 [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)，统一用 classical/text 的 `.list`（DustinWin 均无对应集，路径均不含 `geosite`/`geoip`）：`apple` = `rule/Clash/Apple/Apple.list`；`microsoft` = `rule/Clash/Microsoft/Microsoft.list`；`onedrive` = `rule/Clash/OneDrive/OneDrive.list`（microsoft / onedrive 必须 classical 才能保住 keyword）：

- **Full**：`private` · `privateip` · `google-cn` · `apple-cn` · `apple`（blackmatrix7）· `microsoft-cn` · `microsoft`（blackmatrix7）· `onedrive`（blackmatrix7）· `games-cn` · `ai` · `media` · `games` · `proxy` · `telegramip` · `cn`（映射完整 `cn.mrs`）· `cnip` · `fakeip-filter`（仅供 `dns.fake-ip-filter`）
- **Nano**：`private` · `privateip` · `gfw` · `cn`（映射完整 `cn.mrs`）· `cnip`
- [Koolson/Qure](https://github.com/Koolson/Qure)：策略组图标

## 贡献

如有改进建议或发现规则集变更，欢迎提交 Issue 或 Pull Request。
