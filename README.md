# GlobalScript

GlobalScript 是一份面向 Clash Meta / Mihomo 的精简分流模板。它不追求把每个服务都拆成独立策略组，而是采用更易维护的主线逻辑：**国内默认直连，普通国外流量统一进入代理出口，同时为 AI、流媒体、Google、Apple、Microsoft、开发工具、游戏平台保留少量高价值大类入口，并保留地区节点选择能力**。

## 配置文件

- [`Clash_Full.yaml`](https://raw.githubusercontent.com/WillLiang713/GlobalScript/main/Clash_Full.yaml)：主配置模板，不包含任何代理节点。

> 这是模板配置，不是完整订阅。你需要搭配自己的节点订阅、配置合并功能或手动添加 `proxies` 后使用。

## 设计思路

### 1. 分流规则保持极简

规则层只负责区分几类核心流量：

- 局域网 / 私有地址：`DIRECT`
- 中国大陆相关域名与 IP：`DIRECT`
- 游戏平台：中国区服务直连，下载 CDN 和平台流量进入 `游戏平台`
- 海外 AI 服务：统一进入 `AI出口`
- 流媒体 / 娱乐服务：统一进入 `流媒体`
- Google / Apple / Microsoft 服务：用于普通品牌服务和 Google Play / App Store 等地区控制
- 开发工具：代码托管、包管理器、开发文档等流量进入 `开发工具`
- 普通国外流量：统一进入 `代理出口`
- 最终兜底：统一进入 `代理出口`

这样可以避免社交通讯等服务各自拆成小组导致的选择负担，同时只为 AI、流媒体、Google、Apple、Microsoft、开发工具、游戏平台保留少量确实有独立出口价值的大类入口。规则层使用 ACL4SSR 的 `rule-providers`，减少对客户端内置 `GeoSite.dat` 分类名称的依赖。开发工具和 Google / Apple / Microsoft 规则放在流媒体与游戏平台规则之后，用于控制开发相关流量、普通品牌服务和商店服务的出口地区。

### 2. 出口选择集中到少量大类

`代理出口` 是普通国外流量和最终兜底的主策略组，并被放在代理组列表最前面，方便在 Zashboard / Yacd / MetaCubeXD 等面板中快速选择。AI、流媒体、Google、Apple、Microsoft、开发工具、游戏平台作为少量高价值大类独立保留。

可选出口包括：

- 自动测速
- 手动切换
- 自建节点
- 香港节点
- 美国节点
- 日本节点
- 新加坡节点
- 台湾节点
- 韩国节点
- 其他节点
- DIRECT
- 具体节点

这些大类策略组开启了 `include-all`，所以除了上述快捷分组，也可以直接选择某个具体节点。直接选择具体节点时，选择状态属于当前策略组本身，不会受 `自建节点`、`香港节点` 等共享分组当前选择的影响。

也就是说，**普通国外服务不再拆成大量独立小组，但 AI、流媒体、Google、Apple、Microsoft、开发工具、游戏平台保留大类入口，地区出口也仍然保留**。如果需要临时切换到香港、日本、美国等地区，只需要在对应大类组或 `代理出口` 中选择对应地区即可。

`代理出口`、`AI出口`、`流媒体`、`谷歌服务`、`苹果服务`、`微软服务`、`开发工具`、`游戏平台` 使用统一的候选出口顺序，并通过 `include-all` 提供直接节点选择能力。`自动测速` 是原 `智能优选` 的更准确命名，它只表示根据测试 URL 和延迟进行 `url-test` 自动选择，不代表 IP 质量、AI 可用性或流媒体解锁能力。

### 3. 地区节点自动分类

配置通过 `include-all`、`filter` 和 `exclude-filter` 自动从已有节点中筛选地区节点：

- 香港节点
- 美国节点
- 日本节点
- 新加坡节点
- 台湾节点
- 韩国节点
- 其他节点
- 自建节点

地区组使用 `url-test` 自动测速，适合需要快速选择相对可用线路的场景。

### 4. DNS 覆写保持轻量

模板内置轻量 DNS 配置，适合放入 OpenClash 的 DNS 覆写中使用。DNS 模式、监听端口、IPv6 等运行时开关交由 OpenClash 管理；模板只保留基础上游 DNS 和 `fake-ip-filter`，用于降低局域网发现、系统连通性检测、时间同步和实时通信场景的兼容风险。

## 当前分流逻辑

```yaml
rules:
# 局域网 / 私有地址
- RULE-SET,LocalAreaNetwork,DIRECT

# 游戏平台：国内服务和国内下载节点直连
- RULE-SET,SteamCN,DIRECT

# AI 服务
- RULE-SET,AI,AI出口

# 流媒体 / 娱乐服务
- RULE-SET,ProxyMedia,流媒体

# 游戏平台
- RULE-SET,GameDownload,游戏平台
- RULE-SET,Steam,游戏平台
- RULE-SET,Epic,游戏平台
- RULE-SET,Origin,游戏平台
- RULE-SET,Blizzard,游戏平台
- RULE-SET,Nintendo,游戏平台
- RULE-SET,Sony,游戏平台
- RULE-SET,Xbox,游戏平台

# 开发工具：代码托管、包管理器、开发文档等进入开发工具组
- RULE-SET,Developer,开发工具

# Google / Apple / Microsoft 服务：用于普通品牌服务和商店地区控制
- RULE-SET,Google,谷歌服务
- RULE-SET,Apple,苹果服务
- RULE-SET,Microsoft,微软服务

# 海外常规代理
- RULE-SET,ProxyLite,代理出口

# 国内兜底
- RULE-SET,ChinaDomain,DIRECT
- RULE-SET,ChinaIp,DIRECT
- GEOIP,CN,DIRECT

# 最终兜底
- MATCH,代理出口
```

## 快速使用

1. 下载 [`Clash_Full.yaml`](https://raw.githubusercontent.com/WillLiang713/GlobalScript/main/Clash_Full.yaml)。
2. 将你的节点订阅与该模板合并，或手动补充节点信息。
3. 使用支持 Clash Meta / Mihomo 规则语法的客户端加载配置。
4. 打开控制面板，在 `代理出口`、`AI出口`、`流媒体`、`谷歌服务`、`苹果服务`、`微软服务`、`开发工具` 或 `游戏平台` 中选择自动测速、手动、自建、指定地区出口，或直接选择某个具体节点。

## 适合人群

这个配置适合希望：

- 国内流量稳定直连
- 普通国外流量统一代理
- AI 服务需要固定更稳定、更干净的出口
- 流媒体服务需要按地区单独选择出口
- Google Play / App Store / Microsoft 等品牌服务需要手动选择出口
- 开发工具、代码托管、包管理器等服务需要独立出口
- 游戏平台保留独立入口，便于商店、社区、下载等场景手动切换
- 面板中减少服务类策略组
- 仍然可以按地区选择代理出口
- 配置规则清晰、少维护、容易排错

如果你需要对开发工具、社交通讯等服务分别指定不同节点，可以在此模板基础上自行添加对应策略组和规则。

## 注意事项

- 本配置使用 ACL4SSR 的远程 `rule-providers`，首次加载和定期更新需要客户端能访问对应规则 URL；国内 IP 兜底仍保留 `GEOIP,CN`。
- DNS 块按 OpenClash 覆写场景精简，不包含 `enable`、`listen`、`enhanced-mode`、`fake-ip-range` 等运行时开关；这些选项建议在 OpenClash 界面中管理。
- `Clash_Full.yaml` 不包含节点，直接导入不会产生可用代理。
- 游戏相关流量保留 `游戏平台` 独立入口；`SteamCN` 直连，下载 CDN 和 Steam / Epic / Origin / Blizzard / Nintendo / Sony / Xbox 等平台规则进入 `游戏平台` 以保留手动切换能力。
- `谷歌服务` / `苹果服务` 不再额外叠加 `google-cn`、`google@cn`、`apple-cn`、`apple@cn` 直连规则，以避免 Google Play / App Store 等商店相关请求被提前直连，影响地区切换。
- 流媒体和游戏平台规则优先于 Google / Apple 品牌规则，以便 YouTube、Apple TV+、Apple Music、游戏商店和游戏下载等流量优先进入对应大类入口。
- `开发工具` 使用 ACL4SSR 的 `Developer` 规则，并放在 `Microsoft` 之前，避免 GitHub 等开发流量被微软服务规则提前命中；二者都放在 `ProxyLite` 和国内兜底规则之前。
- 如果某些节点名称无法被地区规则识别，可以调整对应地区组的 `filter`。

## License

本项目以 [MIT License](./LICENSE) 发布。

配置中引用的远程图标、演示配置中的第三方规则与资源不属于本项目授权范围，相关内容版权与使用条款归其各自上游项目或权利方所有。本仓库目前主要引用：

- [`Koolson/Qure`](https://github.com/Koolson/Qure)
- [`Orz-3/mini`](https://github.com/Orz-3/mini)

---

简单分流，集中选择，保留地区自由度。
