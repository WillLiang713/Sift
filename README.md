<h1 align="center">Sift</h1>

<p align="center">
无节点分流模板 · 策略组 / 远程规则 / 分流顺序
</p>

<p align="center">
  <img alt="Rules" src="https://img.shields.io/badge/rules-MRS%20%2F%20list-green?style=flat-square">
  <img alt="Nodes" src="https://img.shields.io/badge/nodes-not%20included-lightgrey?style=flat-square">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-blue?style=flat-square">
</p>

## 模板

| | 说明 |
| --- | --- |
| **[Full](./rules/full.yaml)** | 场景 · 品牌 · 地区 · DNS |
| **[Core](./rules/core.yaml)** | 基础分流 · Apple/Microsoft 服务可切换 · DNS |
| **[Nano](./rules/nano.yaml)** | 极简 · 无 DNS |

```text
https://raw.githubusercontent.com/WillLiang713/Sift/main/rules/full.yaml
https://raw.githubusercontent.com/WillLiang713/Sift/main/rules/core.yaml
https://raw.githubusercontent.com/WillLiang713/Sift/main/rules/nano.yaml
```

Core 的 `苹果服务`、`微软服务` 与 `直连` 默认选择直连；`OneDrive` 域由 `微软服务` 承接（在 Microsoft 集内），`GitHub` 域走 `proxy` 兜底到 `节点选择`（均无独立组/规则），可在面板中切换。Core/Nano 不提供 `手动切换`，所有模板的 `漏网之鱼` 默认选择 `节点选择`。

Full/Core 的海外 DoH 固定跟随 `节点选择`，国内 DoH 与代理节点域名解析固定直连；不提供独立 DNS 策略组。

Full 服务组通过地区组和 `其他节点` 覆盖节点；Core 服务组直接包含全部可用节点（过滤订阅信息节点），Nano 则由 `节点选择` 直接覆盖全部可用节点。动态节点入口统一使用 `include-all`，兼容客户端注入的 `proxies` 与用户自行配置的 `proxy-providers`。

Full 的路由先完成服务、品牌、`proxy` 与 `cn-lite` 等域名分类，再检查流媒体、Telegram 与国内 IP 集；避免普通域名在完成域名规则匹配前被服务 IP 规则触发解析。

## 文档

[DNS](./docs/dns.md) · [规则集](./docs/rulesets.md) · [维护](./AGENTS.md)

## 开源许可

本项目以 [MIT License](./LICENSE) 开源发布，可自由使用、修改与再分发，但须保留版权声明与许可条款。
