# Qure 图标参考手册

> 仓库：[Koolson/Qure](https://github.com/Koolson/Qure) — Quantumult X 策略组图标集
>
> 本文档汇总了 Qure 仓库中所有可用图标及其 CDN 链接格式，供 Mihomo / Clash Meta 配置引用。

## CDN 链接格式

本项目使用 jsDelivr CDN 加速。所有图标路径遵循以下模式：

```
https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/{子目录}/{图标名}.png
```

也可使用 GitHub Raw（不推荐，速度较慢）：

```
https://raw.githubusercontent.com/Koolson/Qure/master/IconSet/{子目录}/{图标名}.png
```

## 图标风格（子目录）

| 目录 | 风格 | 说明 |
|------|------|------|
| `IconSet/` | Classic（经典） | 白色/灰色基调，最早一批图标，部分较旧 |
| `IconSet/Color/` | Color（彩色） | 彩色版本，最常用，也是本项目默认风格 |
| `IconSet/Dark/` | Dark（暗色） | 深色背景适配 |
| `IconSet/mini/` | Mini（迷你） | 小尺寸版本 |

> **本项目当前全部使用 `Color` 风格。** 新策略组优先从 Color 子目录选取。

---

## Sift 项目当前使用的图标

以下为 `Full.yaml` 和 `Nano.yaml` 中已引用的图标：

| 图标名 | CDN 路径 | 对应策略组 |
|--------|----------|-----------|
| `Proxy` | `Color/Proxy.png` | 节点选择 |
| `Available` | `Color/Available.png` | 手动切换 |
| `Auto` | `Color/Auto.png` | 自动测速 |
| `AI` | `Color/AI.png` | AI |
| `ForeignMedia` | `Color/ForeignMedia.png` | 流媒体 |
| `Game` | `Color/Game.png` | 游戏平台 |
| `Apple_1` | `Color/Apple_1.png` | 苹果服务 |
| `Microsoft` | `Color/Microsoft.png` | 微软服务 |
| `OneDrive` | `Color/OneDrive.png` | OneDrive |
| `Hong_Kong` | `Color/Hong_Kong.png` | 香港节点 |
| `US` | `Color/US.png` | 美国节点 |
| `Japan` | `Color/Japan.png` | 日本节点 |
| `Singapore` | `Color/Singapore.png` | 新加坡节点 |
| `Global` | `Color/Global.png` | 其他节点 |
| `Direct` | `Color/Direct.png` | 全球直连 |
| `Final` | `Color/Final.png` | 漏网之鱼 |

---

## Color 风格完整图标列表

### 通用 / 代理

| 图标名 | 说明 |
|--------|------|
| `Proxy` | 代理 / 节点选择 |
| `Auto` | 自动测速 |
| `Available` / `Available_1` | 手动切换 / 可用节点 |
| `Static` / `Static_1` | 静态节点 |
| `Round_Robin` / `Round_Robin_1` | 轮询 |
| `Direct` | 直连 |
| `Global` | 全球 |
| `Final` / `Final_1` | 漏网之鱼 / 最终 |
| `Reject` | 拒绝 |
| `Blackhole` | 黑洞 / 广告拦截 |
| `Bypass` | 绕过 |
| `Unlock` | 解锁 |
| `Domestic` | 国内 |

### 国家 / 地区

| 图标名 | 说明 |
|--------|------|
| `Hong_Kong` / `HK` | 香港 |
| `China` / `CN` | 中国 |
| `China_Map` | 中国地图 |
| `Taiwan` / `TW` | 台湾 |
| `Macao` / `MO` | 澳门 |
| `Japan` / `JP` | 日本 |
| `Korea` / `KR` | 韩国 |
| `Singapore` / `SG` | 新加坡 |
| `United_States` / `US` | 美国 |
| `United_States_Map` | 美国地图 |
| `Canada` / `CA` | 加拿大 |
| `United_Kingdom` / `UK` | 英国 |
| `Germany` / `DE` | 德国 |
| `France` / `FR` | 法国 |
| `Russia` / `RU` | 俄罗斯 |
| `Finland` / `FI` | 芬兰 |
| `Turkey` / `TR` | 土耳其 |
| `Ukraine` / `UA` | 乌克兰 |
| `Brazil` / `BR` | 巴西 |
| `Argentina` / `AR` | 阿根廷 |
| `Egypt` / `EG` | 埃及 |
| `India` / `IN` | 印度 |
| `Thailand` / `TH` | 泰国 |
| `Malaysia` / `MY` | 马来西亚 |
| `Philippines` / `PH` | 菲律宾 |
| `Australia` / `AU` | 澳大利亚 |
| `European_Union` / `EU` | 欧盟 |
| `United_Nations` / `UN` | 联合国 |

### 大洲 / 世界

| 图标名 | 说明 |
|--------|------|
| `Asia_Map` | 亚洲地图 |
| `Europe_Map` | 欧洲地图 |
| `America_Map` | 美洲地图 |
| `Africa_Map` | 非洲地图 |
| `Oceania_Map` | 大洋洲地图 |
| `LA_Map` | 拉丁美洲地图 |
| `World_Map` | 世界地图 |
| `LA` | 拉丁美洲 |

### Apple 生态

| 图标名 | 说明 |
|--------|------|
| `Apple` / `Apple_1` / `Apple_2` | Apple |
| `App_Store` | App Store |
| `Apple_Music` | Apple Music |
| `Apple_TV` / `Apple_TV_Plus` | Apple TV / TV+ |
| `Apple_News` | Apple News |
| `Apple_Fitness` / `Apple_Fitness+` / `Apple_Fitness+_Letter` | Apple Fitness |
| `Apple_Update` | Apple 更新 |
| `iCloud` | iCloud |
| `Siri` | Siri |
| `Find_My` | Find My |
| `TestFlight` / `TestFlight_1` / `TestFlight_2` | TestFlight |

### 流媒体 / 视频

| 图标名 | 说明 |
|--------|------|
| `Netflix` / `Netflix_Letter` | Netflix |
| `YouTube` / `YouTube_Letter` | YouTube |
| `YouTube_Music` | YouTube Music |
| `Disney+` / `Disney+_1` / `Disney+_2` / `Disney` | Disney+ |
| `HBO` / `HBO_1` / `HBO_2` / `HBO_GO` / `HBO_GO_1` / `HBO_GO_2` / `HBO_Max` | HBO / Max |
| `Prime_Video` / `Prime_Video_1` / `Prime_Video_2` | Prime Video |
| `Hulu` / `Hulu_1` | Hulu |
| `Spotify` | Spotify |
| `TikTok` / `TikTok_1` / `TikTok_2` | TikTok |
| `Twitch` | Twitch |
| `TIDAL` / `TIDAL_1` / `TIDAL_2` | TIDAL |
| `KKBOX` | KKBOX |
| `JOOX` / `JOOX_Letter` | JOOX |
| `bilibili` / `bilibili_1` ~ `bilibili_4` | Bilibili |
| `iQIYI` / `iQIYI_1` / `iQIYI&bilibili` | 爱奇艺 |
| `WeTV` / `WeTV_Letter` | WeTV |
| `Bahamut` | 巴哈姆特动画疯 |
| `niconico` / `niconico_1` / `niconico_2` | niconico |
| `encoreTVB` | TVB Anywhere |
| `myTV_SUPER` | myTV SUPER |
| `ViuTV` / `Viu` | ViuTV |
| `LiTV` | LiTV |
| `LineTV` / `LineTV_Letter` | Line TV |
| `friDay` | friDay 影音 |
| `KKTV` | KKTV |
| `AbemaTV` | AbemaTV |
| `deezer` / `deezer_1` / `deezer_2` | Deezer |
| `DAZN` / `DAZN_1` / `DAZN_2` | DAZN |
| `ESPN+` / `ESPN+_1` / `ESPN+_2` | ESPN+ |
| `FOX` | FOX |
| `NBC` | NBC |
| `PBS` | PBS |
| `BBC_iPlayer` / `BBC_iPlayer_1` / `BBC_iPlayer_2` | BBC iPlayer |
| `ITV` / `ITV_1` / `ITV_2` | ITV Hub |
| `My5` | My5 |
| `All4` | All4 |
| `5iTV` | 5iTV |
| `Sling_TV` | Sling TV |
| `fuboTV` | fuboTV |
| `Peacock` / `Peacock_1` / `Peacock_2` / `Peacock_Letter` / `Peacock_P` | Peacock |
| `Paramount` | Paramount+ |
| `Discovery+` | Discovery+ |
| `Star+` / `Star` / `Star_1` / `Star_2` | Star+ |
| `STARZ` | STARZ |
| `Tubi` | Tubi |
| `Vimeo` | Vimeo |
| `Pornhub` / `Pornhub_1` / `Pornhub_2` | Pornhub |
| `HKMTMedia` | 港台媒体 |
| `DomesticMedia` | 国内媒体 |
| `ForeignMedia` | 国外媒体 |
| `Media` | 媒体 |
| `Streaming` / `StreamingCN` / `StreamingSE` / `Streaming!CN` | 流媒体分类 |

### AI / 科技

| 图标名 | 说明 |
|--------|------|
| `AI` | AI 通用 |
| `ChatGPT` | ChatGPT |
| `Copilot` | Microsoft Copilot |
| `Bot` | Bot |

### 游戏平台

| 图标名 | 说明 |
|--------|------|
| `Game` | 游戏通用 |
| `Steam` | Steam |
| `Epic_Games` | Epic Games |
| `PlayStation` / `PlayStation_1` | PlayStation |
| `Xbox` | Xbox |
| `Nintendo` | Nintendo |
| `LOL` / `League_of_Legends` | 英雄联盟 |
| `ARK` | ARK |
| `Ingress` | Ingress |

### 微软 / 云服务

| 图标名 | 说明 |
|--------|------|
| `Microsoft` | Microsoft |
| `OneDrive` | OneDrive |
| `Windows` / `Windows_11` | Windows |
| `Azure` | Azure |
| `GitHub` / `GitHub_Letter` | GitHub |
| `Linkedin` | LinkedIn |
| `Notion` | Notion |

### 社交 / 通讯

| 图标名 | 说明 |
|--------|------|
| `Telegram` / `Telegram_X` | Telegram |
| `Twitter` / `X` | Twitter / X |
| `Facebook` | Facebook |
| `Instagram` | Instagram |
| `Discord` | Discord |
| `WeChat` | 微信 |
| `QQ` | QQ |
| `Weibo` | 微博 |
| `Line` | Line |
| `Kakao` | Kakao Talk |
| `Clubhouse` / `Clubhouse_1` / `Clubhouse_2` | Clubhouse |
| `Gmail` | Gmail |
| `Mail` | 邮件 |

### 运营商 / ISP

| 图标名 | 说明 |
|--------|------|
| `Cloudflare` | Cloudflare |
| `China_Telecom` | 中国电信 |
| `China_Unicom` | 中国联通 |
| `CMI` | 中国移动国际 |
| `HGC` | 和记环球电讯 |
| `HKT` | 香港电讯 |
| `HKBN` | 香港宽频 |
| `PCCW` | 电讯盈科 |
| `CTM` | 澳门电讯 |
| `CHT` | 中华电信 |
| `HiNet` | HiNet |
| `NTT` | NTT |
| `IIJ` | IIJ |
| `SoftBank` / `SoftBank_Letter` | SoftBank |
| `KT` | KT |
| `WTT` | WTT |
| `CMI` | CMI |

### 专线 / 中转

| 图标名 | 说明 |
|--------|------|
| `IEPL` | IEPL 专线 |
| `IPLC` | IPLC 专线 |
| `CN2` / `CN2_GIA` / `CN2_GT` / `GIA` / `GT` | CN2 / GIA / GT |
| `BGP` | BGP |

### 代理协议

| 图标名 | 说明 |
|--------|------|
| `SSL` | SSL |
| `Trojan` / `Trojan_Letter` | Trojan |
| `VMess` / `VMess_Letter` | VMess |
| `SS` / `SS_Letter` | Shadowsocks |
| `SSR` / `SSR_Letter` | SSR |

### 机场 / 服务商

| 图标名 | 说明 |
|--------|------|
| `Airport` | 机场通用 |
| `AmyTelecom` / `AmyTelecom_1` | AmyTelecom |
| `BosLife` / `BosLife_1` / `BosLife_Letter` | BosLife |
| `Blinkload` / `Blinkload_1` / `Blinkload_B` / `Blinkload_SS` / `Blinkload_V2Ray` | Blinkload |
| `Catnet` | Catnet |
| `Dler` | Dler |
| `GLaDOS` | GLaDOS |
| `Nexitally` | Nexitally |
| `Nfcloud` | Nfcloud |
| `rixcloud` / `rix` | RixCloud |
| `ssrcloud` | SSRCloud |
| `ssLinks` | ssLinks |
| `YTOO` / `YTOO_Letter` | YTOO |
| `YoYu` / `YoYu_Letter` | YoYu |
| `CreamData` | CreamData |
| `LinkCube` | LinkCube |
| `TAG` | TAG |
| `ULB` / `ULB_1` / `ULB_Alt` | ULB |
| `Naiko` | Naiko |
| `Renzhe` | Renzhe |
| `Ryan` | Ryan |
| `Pirate_Nation` | Pirate Nation |
| `Null_Nation` | Null Nation |
| `Want_Want` / `Want_Want_1` / `Want_Want_Letter` | Want Want |

### 云平台

| 图标名 | 说明 |
|--------|------|
| `AWS` | Amazon Web Services |
| `GCP` | Google Cloud Platform |
| `Oracle` | Oracle Cloud |
| `Alibaba_Cloud` | 阿里云 |
| `Tencent_Cloud` | 腾讯云 |
| `Alibaba` | 阿里巴巴 |

### 支付 / 购物

| 图标名 | 说明 |
|--------|------|
| `PayPal` | PayPal |
| `Taobao` | 淘宝 |
| `Amazon` / `Amazon_1` | Amazon |

### 音乐

| 图标名 | 说明 |
|--------|------|
| `Music_Enhance` | 音乐增强 |
| `Netease_Music` | 网易云音乐 |
| `Netease_Music_Unlock` | 网易云解锁 |
| `Pandora` | Pandora |

### 其他工具

| 图标名 | 说明 |
|--------|------|
| `Speedtest` | Speedtest |
| `Download` | 下载 |
| `Emby` | Emby |
| `Infuse` / `Infuse_7` | Infuse |
| `Cydia` | Cydia |
| `Quantumult_X` | Quantumult X |
| `Qure` | Qure |
| `Sch` | Scholar |
| `Stack` | Stack |
| `Filter` | 过滤 |
| `AdBlack` / `AdWhite` / `Advertising` | 广告拦截 |
| `Loop` | 循环 |
| `Server` | 服务器 |
| `SSID` / `SSID_1` / `SSID_Alt` | SSID |
| `WiFi` | WiFi |
| `Cellular` | 蜂窝网络 |
| `Lock` | 锁定 |
| `Puzzle` | 拼图 |
| `Lab` | 实验室 |
| `Area` | 区域 |
| `Magic` | 魔法 |
| `Spark` | 火花 |
| `Star` | 星星 |
| `Heart` | 爱心 |
| `Rainbow` / `Rainbow_1` | 彩虹 |
| `Fries` | 薯条 |
| `VIP` | VIP |
| `Back` | 返回 |
| `Daily` | 日常 |
| `Drill` | 钻头 |
| `Rocket` | 火箭 |
| `Lambda` | Lambda |
| `Bookpedia` | 书籍 |
| `Scholar` | 学术 |
| `PostBox` / `PostBox_1` / `PostBox_Alt` | 邮箱 |
| `Mouse` | 鼠标 |
| `Dinosaur` | 恐龙 |
| `Flamingo` | 火烈鸟 |
| `Frog` | 青蛙 |
| `Cat` | 猫 |
| `Pig` | 猪 |
| `Ox` | 牛 |
| `Luffy` | 路飞 |
| `Apeach` | Apeach |
| `Bamboo` | 竹子 |
| `Brown` | Brown |
| `Mickey` | 米奇 |
| `Ninja` | 忍者 |
| `Ring` | 戒指 |
| `Libra` | 天秤 |

### 加密货币

| 图标名 | 说明 |
|--------|------|
| `Cryptocurrency` / `Cryptocurrency_1` / `Cryptocurrency_2` / `Cryptocurrency_3` | 加密货币 |

### 备选编号标记（x 系列 / ＊ 系列）

用于区分同一类别的多个实例，按倍率排列：

| 图标名 | 倍率 |
|--------|------|
| `x0` | 0 |
| `x0.1` | 0.1 |
| `x0.2` | 0.2 |
| `x0.3` | 0.3 |
| `x0.4` | 0.4 |
| `x0.5` | 0.5 |
| `x0.7` | 0.7 |
| `x1` / `x1.0` | 1.0 |
| `x2` / `x2.0` | 2.0 |
| `x3` / `x3.0` | 3.0 |
| `x4.0` | 4.0 |
| `x5.0` | 5.0 |
| `＊0` | 0 |
| `＊0.1` | 0.1 |
| `＊0.3` | 0.3 |
| `＊0.5` | 0.5 |
| `＊1` | 1 |
| `＊2` | 2 |
| `＊3` | 3 |

---

## Qure 仓库结构

```
Koolson/Qure/
├── IconSet/           ← Classic 风格（原始白色/灰色图标）
│   ├── Color/         ← 彩色图标（本项目使用）
│   ├── Dark/          ← 暗色图标
│   └── mini/          ← 迷你图标
├── Other/             ← 预览图、Logo 等
└── README.md
```

## 注意事项

1. **文件名区分大小写**，如 `Hong_Kong.png` 不可写为 `hong_kong.png`。
2. **下划线与短横线不可混用**，如 `Apple_TV_Plus` 和 `BBC_iPlayer`。
3. 带 `+` 的图标名需 URL 编码：`Apple_Fitness%2B.png`，或在 jsDelivr 中直接使用原字符 `Apple_Fitness+.png`（jsDelivr 会自动处理）。
4. Color 子目录比 Classic 根目录多了部分图标（如 `ChatGPT`、`Copilot`、`AI`、`Discord`、`Steam` 等），新增策略组优先从这里选用。
5. 本项目 AGENTS.md 规定图标引用仅限 `Koolson/Qure`，不得随意切换至其他图标仓库。

## 参考链接

- 仓库主页：https://github.com/Koolson/Qure
- IconSet 目录：https://github.com/Koolson/Qure/tree/master/IconSet
- Color 子目录：https://github.com/Koolson/Qure/tree/master/IconSet/Color
- 归档图标预览：https://raw.githubusercontent.com/Koolson/Qure/master/Other/Qure_Preview_Archived.png
- 全部效果图预览：https://raw.githubusercontent.com/Koolson/Qure/master/Other/Qure_Preview_All.png
