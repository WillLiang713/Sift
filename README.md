# Sift

Sift 是一组面向 Mihomo 的精简分流模板：国内默认直连，GFW 命中流量进入节点选择，只为确实需要单独调节的场景保留策略组。

> 模板不包含任何代理节点。请搭配自己的节点订阅、配置合并功能，或手动补充 `proxies` 后使用。

## 模板

| 文件 | 定位 | 保留的主要策略组 |
| --- | --- | --- |
| [`Full.yaml`](https://raw.githubusercontent.com/WillLiang713/Sift/main/Full.yaml) | 完整精简版 | `节点选择`、`自动测速`、`漏网之鱼`、`AI出口`、`流媒体`、`谷歌服务`、`苹果服务`、`微软服务`、`开发工具`、`游戏平台`、地区节点组 |
| [`Mini.yaml`](https://raw.githubusercontent.com/WillLiang713/Sift/main/Mini.yaml) | 日常极简版 | `节点选择`、`自动测速`、`AI出口`、`流媒体`、`漏网之鱼` |

## 分流逻辑

### Full.yaml

| 流量 | 出口 |
| --- | --- |
| 局域网、私有地址、中国大陆域名与 IP | `DIRECT` |
| Steam 中国区、国内游戏平台、GoogleCN、AppleCN、Microsoft CN | `DIRECT` |
| AI 服务 | `AI出口` |
| 流媒体 / 娱乐服务 | `流媒体` |
| Steam、Epic、Origin、Blizzard、Nintendo、Sony、Xbox 等游戏平台 | `游戏平台` |
| GitHub、开发工具、包管理器、开发文档 | `开发工具` |
| Google / Apple / Microsoft 服务 | `谷歌服务` / `苹果服务` / `微软服务` |
| GFW 命中流量 | `节点选择` |
| 未命中规则 | `漏网之鱼` |

### Mini.yaml

| 流量 | 出口 |
| --- | --- |
| 局域网、私有地址、中国大陆域名与 IP | `DIRECT` |
| Steam 中国区、国内游戏平台、GoogleCN、AppleCN、Microsoft CN | `DIRECT` |
| AI 服务 | `AI出口` |
| 流媒体 / 娱乐服务 | `流媒体` |
| GFW 命中流量 | `节点选择` |
| 未命中规则 | `漏网之鱼` |

## 选择建议

- 选 `Full.yaml`：需要 Google、Apple、Microsoft、开发工具、游戏平台或地区节点组单独调节。
- 选 `Mini.yaml`：希望面板尽量清爽，只保留普通代理、AI、流媒体和兜底出口。

## 使用

1. 下载 `Full.yaml` 或 `Mini.yaml`。
2. 将模板与自己的节点订阅合并，或手动补充 `proxies`。
3. 使用支持 Mihomo `rule-providers` / `RULE-SET` 规则语法的客户端加载配置。
4. 在策略组中选择 `自动测速`、`节点选择`、地区组或具体节点。

## 注意事项

- 模板使用 ACL4SSR 远程 `rule-providers`，首次加载或规则更新时需要客户端能访问 GitHub Raw。
- ACL4SSR 的中国 IP 规则作为国内兜底，用于补充未被国内域名规则覆盖的流量。
- DNS 块按 OpenClash 覆写场景精简，不包含 `enable`、`listen`、`enhanced-mode`、`fake-ip-range` 等运行时开关。
- `Mini.yaml` 不保留地区节点组；需要指定地区时，直接在 `节点选择`、`AI出口`、`流媒体` 或 `漏网之鱼` 中选择具体节点。
- `Full.yaml` 中流媒体和游戏平台规则优先于 Google / Apple 品牌规则，开发工具规则优先于 Microsoft 规则。

## License

本项目以 [MIT License](./LICENSE) 发布。

配置中引用的远程规则、图标、演示配置中的第三方规则与资源不属于本项目授权范围，相关内容版权与使用条款归其各自上游项目或权利方所有。本仓库目前主要引用：

- [`ACL4SSR/ACL4SSR`](https://github.com/ACL4SSR/ACL4SSR)：远程分流规则来源。
- [`Koolson/Qure`](https://github.com/Koolson/Qure)
- [`Orz-3/mini`](https://github.com/Orz-3/mini)
