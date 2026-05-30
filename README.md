# Sift

Sift 是一组面向 Mihomo 的精简分流模板：国内默认直连，以 DustinWin MRS 规则为主干，`Full.yaml` 额外用 blackmatrix7 补充专用场景分流，只为确实需要单独调节的场景保留策略组。

> 模板不包含任何代理节点。请搭配自己的节点订阅、配置合并功能，或手动补充 `proxies` 后使用。

## 模板

| 文件 | 定位 | 远程链接 | 保留的主要策略组 |
| --- | --- | --- | --- |
| `Full.yaml` | 完整精简版 | `https://raw.githubusercontent.com/WillLiang713/Sift/main/Full.yaml` | `节点选择`、`自动测速`、`漏网之鱼`、`AI`、`流媒体`、`谷歌服务`、`苹果服务`、`微软服务`、`开发工具`、`游戏平台`、地区节点组 |
| `Mini.yaml` | 日常极简版 | `https://raw.githubusercontent.com/WillLiang713/Sift/main/Mini.yaml` | `节点选择`、`自动测速`、`AI`、`流媒体`、`漏网之鱼` |

## 分流逻辑

### Full.yaml

| 流量 | 出口 |
| --- | --- |
| 局域网、私有地址、中国大陆域名与 IP | `DIRECT` |
| Google / Apple / Microsoft 中国区、国内游戏服务 | `DIRECT` |
| AI 服务 | `AI` |
| 流媒体 / 娱乐服务 | `流媒体` |
| Steam、Epic、Origin、Blizzard、Nintendo、Sony、Xbox 等游戏平台 | `游戏平台` |
| GitHub、开发工具、包管理器、开发文档 | `开发工具` |
| Google / Apple / Microsoft 服务 | `谷歌服务` / `苹果服务` / `微软服务` |
| GFW 轻量代理规则命中流量 | `节点选择` |
| 未命中规则 | `漏网之鱼` |

### Mini.yaml

| 流量 | 出口 |
| --- | --- |
| 局域网、私有地址、中国大陆域名与 IP | `DIRECT` |
| Google / Apple / Microsoft 中国区、国内游戏服务 | `DIRECT` |
| AI 服务 | `AI` |
| 流媒体 / 娱乐服务 | `流媒体` |
| GFW 轻量代理规则命中流量 | `节点选择` |
| 未命中规则 | `漏网之鱼` |

## 选择建议

- 选 `Full.yaml`：需要游戏平台、地区节点组，或希望保留 Google、Apple、Microsoft、开发工具策略组以便手动选择和后续自定义规则。
- 选 `Mini.yaml`：希望面板尽量清爽，只保留普通代理、AI、流媒体和兜底出口。

## 使用

1. 复制上方 `Full.yaml` 或 `Mini.yaml` 远程链接，或下载对应模板文件。
2. 将模板与自己的节点订阅合并，或手动补充 `proxies`。
3. 使用支持 Mihomo `rule-providers` / `RULE-SET` 规则语法的客户端加载配置。
4. 在策略组中选择 `自动测速`、`节点选择`、地区组或具体节点。

## 注意事项

- 模板远程 `rule-providers` 以 DustinWin MRS 规则源为主，并显式提供 `cn-lite` 用于兼容 ShellCrash 等客户端的 DNS `rule-set:cn` 引用；首次加载或规则更新时需要客户端能访问 GitHub Releases 和 GitHub Raw。
- DustinWin 的 `cn-lite` / `cnip` MRS 规则分别作为国内域名和 IP 兜底；`google-cn`、`apple-cn`、`microsoft-cn`、`games-cn` 用于国内服务前置直连。
- `Full.yaml` 使用 blackmatrix7 补充 GitHub、开发工具、Google、Apple、Microsoft 专用规则；`Mini.yaml` 继续只保留 DustinWin 主干规则。
- DNS 块按配置覆写场景精简，不包含 `enable`、`listen`、`enhanced-mode`、`fake-ip-range` 等运行时开关。
- `Mini.yaml` 不保留地区节点组；需要指定地区时，直接在 `节点选择`、`AI`、`流媒体` 或 `漏网之鱼` 中选择具体节点。
- `Full.yaml` 中 AI、流媒体和游戏平台规则优先于 GFW 轻量代理规则。

## License

本项目以 [MIT License](./LICENSE) 发布。

配置中引用的远程规则、图标、演示配置中的第三方规则与资源不属于本项目授权范围，相关内容版权与使用条款归其各自上游项目或权利方所有。本仓库目前主要引用：

- [`DustinWin/ruleset_geodata`](https://github.com/DustinWin/ruleset_geodata)：远程 MRS 分流规则主来源。
- [`blackmatrix7/ios_rule_script`](https://github.com/blackmatrix7/ios_rule_script)：`Full.yaml` 专用场景分流规则来源。
- [`Koolson/Qure`](https://github.com/Koolson/Qure)
- [`Orz-3/mini`](https://github.com/Orz-3/mini)
