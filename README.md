<h1 align="center">Sift</h1>

<p align="center">
面向 Mihomo 的无节点分流配置模板。Sift 只提供策略组、远程规则提供商和分流顺序，不内置任何机场节点、订阅地址或私有 DNS 配置。你可以把它作为订阅转换后的基础模板，再由客户端、订阅合并工具或手动配置补充 `proxies`。
</p>

<p align="center">
  <img alt="Mihomo" src="https://img.shields.io/badge/Mihomo-compatible-blue">
  <img alt="Rules" src="https://img.shields.io/badge/rules-MRS-green">
  <img alt="Node Free" src="https://img.shields.io/badge/nodes-not%20included-lightgrey">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-blue">
</p>

## 适合谁

Sift 适合想把代理配置拆成「节点订阅」和「分流模板」两部分管理的用户：

- 不想在公开仓库里维护个人节点、订阅链接或 DNS 细节。
- 希望 AI、娱乐内容、游戏平台、开发工具、Google、Apple、Microsoft 等服务有独立出口。
- 希望保留最终兜底策略组，避免未命中流量被静默直连造成泄露风险。
- 使用 UU、迅游等游戏加速器时，希望游戏相关流量仍保留可控入口，不被兜底代理抢走。
- 想要一份可以直接作为 Mihomo 模板引用的轻量 YAML。

## 模板选择

| 文件 | 定位 | 策略组 | 规则提供商 | 适用场景 |
| --- | --- | ---: | ---: | --- |
| [`Full.yaml`](./Full.yaml) | 完整模板 | 17 | 16 | 日常主力配置，需要细分 AI、娱乐内容、品牌服务、开发工具、游戏平台和地区节点。 |
| [`Mini.yaml`](./Mini.yaml) | 极简模板 | 5 | 11 | 简化面板，只保留节点选择、自动测速、AI、娱乐内容和兜底。 |

### Raw 链接

```text
https://raw.githubusercontent.com/WillLiang713/Sift/main/Full.yaml
```

```text
https://raw.githubusercontent.com/WillLiang713/Sift/main/Mini.yaml
```

## 核心设计

### 无节点模板

`Full.yaml` 和 `Mini.yaml` 都不包含 `proxies`。模板默认依赖 Mihomo 的 `include-all: true`，由客户端或订阅合并后的节点列表填充策略组。

建议把 Sift 放在订阅转换、配置覆写或客户端模板位置使用，而不是直接当作完整配置导入。使用前需要确保最终配置里已经有节点。

### 不接管 DNS

模板不写顶层 `dns`、`fake-ip` 等全局网络行为。原因是不同客户端、系统和加速器环境差异很大，DNS 更适合放在本地客户端配置中管理。

### 保留兜底出口

未命中规则会进入 `漏网之鱼`，而不是直接 `DIRECT`。这样可以在面板里看到并控制未知流量，降低误直连和 DNS 泄露风险。

### 游戏流量单独处理

国内游戏平台规则直连；境外游戏平台在 `Full.yaml` 中进入 `游戏平台` 策略组。这样既能保留 Steam、Epic、PlayStation、Xbox 等商店/社区访问能力，也不会把所有游戏相关流量粗暴塞进最终兜底。

如果你使用游戏加速器，建议在 `游戏平台` 中按实际环境选择 `DIRECT` 或指定出口，避免和加速器抢路由。

## 分流顺序

### Full.yaml

1. 局域网 / 私有地址 -> `DIRECT`
2. 国内 Google / Apple / Microsoft / 游戏规则 -> `DIRECT`
3. AI 服务 -> `AI`
4. 游戏平台 -> `游戏平台`
5. 娱乐内容 -> `娱乐内容`
6. 开发工具 -> `开发工具`
7. Google / Apple / Microsoft 普通服务 -> `谷歌服务` / `苹果服务` / `微软服务`
8. GFW 轻量代理规则 -> `节点选择`
9. 国内域名 / 国内 IP 兜底 -> `DIRECT`
10. 其他未命中流量 -> `漏网之鱼`

### Mini.yaml

1. 局域网 / 私有地址 -> `DIRECT`
2. 国内 Google / Apple / Microsoft / 游戏规则 -> `DIRECT`
3. AI 服务 -> `AI`
4. 娱乐内容 -> `娱乐内容`
5. GFW 轻量代理规则 -> `节点选择`
6. 国内域名 / 国内 IP 兜底 -> `DIRECT`
7. 其他未命中流量 -> `漏网之鱼`

## 策略组说明

### 通用策略组

- `节点选择`：手动选择具体节点。
- `自动测速`：按 `https://cp.cloudflare.com/generate_204` 测速自动选择低延迟节点。
- `AI`：OpenAI、Claude、Gemini 等 AI 服务统一入口。
- `娱乐内容`：视频、音乐、直播、社交娱乐等内容服务入口。
- `漏网之鱼`：最终兜底出口，用来接住未命中规则的流量。

### Full.yaml 额外策略组

- `谷歌服务`：Google Play、Gmail、Drive、Search 等普通 Google 服务。
- `苹果服务`：App Store、iCloud、iTunes 等 Apple 服务。
- `微软服务`：Microsoft、OneDrive、Office、Windows Update 等服务。
- `开发工具`：GitHub、代码托管、包管理器、开发文档等流量。
- `游戏平台`：Steam、Epic、PlayStation、Xbox 等游戏平台相关流量。
- `香港节点` / `美国节点` / `日本节点` / `新加坡节点` / `台湾节点` / `韩国节点` / `其他节点`：按节点名称关键词自动归类的地区组。

## 节点命名建议

地区组依赖节点名称里的地区关键词过滤。自建节点或手动补充节点时，建议在名称中保留地区信息：

```text
自建-HK-01
自建-日本-东京
US-LosAngeles-01
SG-Relay-01
```

如果节点名称没有地区关键词，它通常会落到 `其他节点` 或只通过 `include-all` 出现在可选列表中。

## 规则来源

Sift 使用远程 MRS 规则集，不把规则文件提交进仓库。

- DustinWin MRS：私有地址、国内服务、国内域名/IP、AI、游戏、GFW。
- MetaCubeX MRS：娱乐内容，以及 `Full.yaml` 的开发工具、Google、Apple、Microsoft。
- Koolson/Qure、Orz-3/mini：策略组图标。

`rule-providers` 名称与规则文件名保持一致，例如 `category-dev` 对应 `category-dev.mrs`，`google` 对应 `google.mrs`，`category-entertainment` 对应 `category-entertainment.mrs`。

## 使用方式

### 作为远程模板引用

1. 复制 `Full.yaml` 或 `Mini.yaml` 的 Raw 链接。
2. 在支持 Mihomo 配置模板、覆写或订阅转换的工具中引用它。
3. 与你的节点订阅合并，或在最终配置中手动补充 `proxies`。
4. 使用支持 `rule-providers`、`RULE-SET` 和 `mrs` 规则格式的 Mihomo 客户端加载最终配置。

### 直接下载后修改

```bash
git clone https://github.com/WillLiang713/Sift.git
cd Sift
```

然后按需要编辑：

- `Full.yaml`：完整分流模板。
- `Mini.yaml`：极简分流模板。
- `scripts/convert.js`：链式代理节点生成脚本。

## 链式代理脚本

`scripts/convert.js` 是一个 JavaScript operator，用来根据传入参数生成「中转 -> 落地」的链式代理节点。

参数：

- `relay`：中转节点名称。
- `landing`：落地节点名称。
- `name`：可选，新生成的链式节点名称。

示例参数：

```text
relay=中转节点名&landing=落地节点名&name=自定义链式名
```

也可以使用脚本支持的别名参数：

- `relay_name` / `transit` / `upstream` / `dialer`
- `landing_name` / `exit` / `downstream` / `proxy`
- `chain_name` / `new_name`

脚本会复制落地节点，并为复制出的节点添加：

```yaml
underlying-proxy: <relay>
```

## 本地验证

仓库没有依赖安装步骤，也没有构建产物。修改模板或脚本后建议运行：

```bash
node --check scripts/convert.js
mihomo -t -f Full.yaml
mihomo -t -f Mini.yaml
git diff --check
```

如果本机没有安装 Mihomo，可以先跳过 `mihomo -t`，但提交前最好在目标客户端或 Mihomo 二进制上验证一次。

## 兼容性说明

使用 Sift 前，请确认你的客户端支持：

- Mihomo 核心或兼容 Mihomo 配置语法的内核。
- `rule-providers`。
- `RULE-SET`。
- `format: mrs`。
- 策略组 `include-all`。
- 地区组使用的 `filter` 关键词匹配。

不同客户端对覆写、订阅合并、图标展示和 JavaScript operator 的支持不完全一致。如果导入后面板不显示图标或脚本不生效，优先检查客户端能力，而不是分流规则本身。

## 目录结构

```text
.
├── Full.yaml                 # 完整 Mihomo 分流模板
├── Mini.yaml                 # 极简 Mihomo 分流模板
├── scripts/
│   └── convert.js            # 链式代理节点生成脚本
├── demo/                     # 示例 / 对照配置
├── AGENTS.md                 # 维护约定
└── LICENSE
```

## 维护原则

- 不提交个人节点、订阅 URL、账号、Token 或私有端点。
- 保持模板无节点，节点由用户自己的订阅或本地配置提供。
- 不在模板中强行接管 DNS / fake-ip。
- 保留 `漏网之鱼` 作为最终兜底出口。
- `Mini.yaml` 保持克制，不加入品牌、开发、游戏和地区节点组。
- `Full.yaml` 的场景策略组尽量保持相同候选列表和顺序，避免某些分组行为特殊化。
- 调整规则顺序时，优先考虑更具体的服务规则，避免被宽泛品牌规则提前命中。

## License

本项目以 [MIT License](./LICENSE) 发布。

远程规则、图标和示例来源属于各自上游项目；使用前请遵守对应项目的许可与使用条款。
