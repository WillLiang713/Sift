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

也可按不同规则源选用独立模板：[rules/variants](./rules/variants/)

Core 的 `苹果服务`、`微软服务` 与 `直连` 默认选择直连；`OneDrive`、`GitHub` 各有独立策略组并默认选择 `节点选择`，均可在面板中切换。所有模板的 `漏网之鱼` 默认选择 `自动测速`。

## 文档

[DNS](./docs/dns.md) · [规则集](./docs/rulesets.md) · [维护](./AGENTS.md)

## 开源许可

本项目以 [MIT License](./LICENSE) 开源发布，可自由使用、修改与再分发，但须保留版权声明与许可条款。
