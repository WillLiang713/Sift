<h1 align="center">Sift</h1>

<p align="center">无节点 Mihomo 分流模板</p>

<p align="center">
  <img alt="Rules" src="https://img.shields.io/badge/rules-MRS-green?style=flat-square">
  <img alt="Nodes" src="https://img.shields.io/badge/nodes-not%20included-lightgrey?style=flat-square">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-blue?style=flat-square">
</p>

## 规则模板

| 文件 | 模式 | 说明 |
| --- | --- | --- |
| [core.yaml](./rules/core.yaml) | 大陆白名单 | 国内服务直连，其余走节点选择。 |
| [gfwlist.yaml](./rules/gfwlist.yaml) | GFWlist | GFWlist 域名走节点，其余直连。 |
| [full.yaml](./rules/full.yaml) | 完整服务组 | 按国内、AI、流媒体、游戏和 Telegram 等服务分组。 |

规则集会从上游自动更新，配置不包含节点。

## 开源许可

本项目以 [MIT License](./LICENSE) 开源发布，可自由使用、修改与再分发，但须保留版权声明与许可条款。
