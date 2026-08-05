# demo/

第三方 / 上游 Mihomo（Clash Meta）YAML 示例，仅供对照阅读与手工对比，**不是**本仓库的无节点分流模板。

可直接使用的模板在 [`../rules/`](../rules/)（`full` / `core` / `nano`）。

## 文件一览

| 文件 | 上游 | 体量 | 适合对照什么 |
| --- | --- | --- | --- |
| [`config.yaml`](./config.yaml) | [MetaCubeX/mihomo `docs/config.yaml`](https://github.com/MetaCubeX/mihomo/blob/Meta/docs/config.yaml) | 大 | 官方全字段语法与能力清单（代理协议、DNS、TUN、sniffer、listeners 等） |
| [`metacubexd-minimal.yaml`](./metacubexd-minimal.yaml) | [MetaCubeX/metacubexd `docs/config.yaml`](https://github.com/MetaCubeX/metacubexd/blob/main/docs/config.yaml) | 极小 | 最小可跑配置：回环、无 provider、`MATCH,DIRECT` |
| [`ACL4SSR-GeneralClashConfig.yml`](./ACL4SSR-GeneralClashConfig.yml) | [ACL4SSR/ACL4SSR `Clash/GeneralClashConfig.yml`](https://github.com/ACL4SSR/ACL4SSR/blob/master/Clash/GeneralClashConfig.yml) | 中 | 经典 ACL4SSR 内嵌规则写法，与 Sift 的远程 rule-providers 思路对比 |
| [`BSakura-Miku-mihomo-template.yml`](./BSakura-Miku-mihomo-template.yml) | [BSakura-Miku/mihomo-config](https://github.com/BSakura-Miku/mihomo-config) | 中 | 现代网关 / 透明代理向模板；订阅 URL 已为占位符 |
| [`Keviin560-mihomo-dns.yaml`](./Keviin560-mihomo-dns.yaml) | [Keviin560/Shunt_Rules `mihomo-dns.yaml`](https://github.com/Keviin560/Shunt_Rules/blob/main/mihomo-dns.yaml) | 中 | 重 DNS + MRS `rule-providers` + 地区策略组的社区写法 |
| [`yingxiaomo-fakeip.yaml`](./yingxiaomo-fakeip.yaml) | [yingxiaomo/Mihomo-Personal-Rules `configs/fakeip.yaml`](https://github.com/yingxiaomo/Mihomo-Personal-Rules/blob/main/configs/fakeip.yaml) | 中 | Fake-IP 全量配置，规则侧大量引用 DustinWin `ruleset_geodata`（与 Sift DustinWin 源相近）；订阅为占位 |

## 使用注意

- 这些文件可能包含 **示例节点 / 占位订阅 / 实验字段**，不要当生产配置直接启用。
- 本仓库 `rules/*` 刻意 **无节点**；demo 中的 `proxies` / `proxy-providers` 仅作结构参考。
- 第三方内容版权归原作者。ACL4SSR 为 **CC BY-SA 4.0**，再分发时请保留署名与相同许可。MetaCubeX 相关文件为 **MIT**。其余社区文件以各自仓库声明为准（抓取时可能未声明 SPDX）。
- 更新方式：从上游 raw / release 重新拉取后替换对应文件，并保留文件头的 `Sift demo snapshot` 说明行。

## 未收录但可自行查看的 GitHub 来源

| 仓库 | 说明 | 未收录原因 |
| --- | --- | --- |
| [Accademia/Clash_Configuration_Template](https://github.com/Accademia/Clash_Configuration_Template) | 高星「省电」完整模板 | 单文件约 700KB+，规则内嵌过重 |
| [zuluion/Clash-Template-Config](https://github.com/zuluion/Clash-Template-Config) | Jinja2 型 Clash 模板 | 不是纯可运行 YAML，且偏旧版 Clash |
| [ACL4SSR/ACL4SSR `Clash/config/*.ini`](https://github.com/ACL4SSR/ACL4SSR/tree/master/Clash/config) | 在线订阅转换用 ini 片段 | 不是完整 Mihomo YAML |
| [MetaCubeX/mihomo 官方文档](https://wiki.metacubex.one/) | 字段说明与片段 | 以文档站为准，不必整站镜像 |

若需要再补某一类（例如仅 TUN、仅 geodata `GEOSITE`、或 OpenClash 专用片段），说明用途后可继续从 GitHub 筛选进本目录。
