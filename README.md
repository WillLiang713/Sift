<h1 align="center">Sift</h1>

<p align="center">
无节点分流模板 · 大陆白名单、GFWlist 与完整服务组
</p>

<p align="center">
  <img alt="Rules" src="https://img.shields.io/badge/rules-MRS-green?style=flat-square">
  <img alt="Nodes" src="https://img.shields.io/badge/nodes-not%20included-lightgrey?style=flat-square">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-blue?style=flat-square">
</p>

## 模板

| 文件 | 模式 | 说明 |
| --- | --- | --- |
| **[core.yaml](./rules/core.yaml)** | 大陆白名单 | 私有地址、大陆域名与国内游戏服务（DustinWin `games-cn`，含 Steam 下载 CDN）直连；`proxy` 先于 `cn`，其余走节点选择。 |
| **[gfwlist.yaml](./rules/gfwlist.yaml)** | GFWlist | 仅 GFWlist 域名走节点选择，其余直连。 |
| **[full.yaml](./rules/full.yaml)** | 完整服务组 | 国内直连（含 apple-cn / microsoft-cn / google-cn / games-cn），AI / 流媒体 / 游戏 / Telegram 独立成组，未收录走漏网之鱼。 |

`core.yaml` 与 `gfwlist.yaml` 只保留“节点选择”“自动测速”两个组。`full.yaml` 另有地区组与服务组。三档都用 fake-ip 规则模式：需要代理的域名返回 fake-IP，直连域名返回真实 IP。三档都开启 HTTP / TLS / QUIC 嗅探：纯 IP 连接按 Host / SNI 匹配规则，仅 HTTP 用嗅探结果覆盖目标。模板需配合客户端导入节点使用。

## 文档

[DNS](./docs/dns.md) · [规则集](./docs/rulesets.md) · [维护](./AGENTS.md)

## 开源许可

本项目以 [MIT License](./LICENSE) 开源发布，可自由使用、修改与再分发，但须保留版权声明与许可条款。
