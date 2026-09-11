# DNS 设计

当前模板为 [core.yaml](../rules/core.yaml)（大陆白名单）与 [gfwlist.yaml](../rules/gfwlist.yaml)（GFWlist）。两档共用 fake-IP 地址池、“代理域名走海外 DoH”的分工和映射持久化，区别只在“谁需要代理”。

- 两档都使用 `fake-ip` 规则过滤：只有需要代理的域名返回 fake-IP，直连域名返回真实 IP。
- IPv4 fake-IP 地址池为 `198.18.0.1/16`，开启映射持久化。
- `core.yaml`：`private`、全量 `cn`（DustinWin `cn.mrs`，不用 `cn-lite`）返回真实 IP，`MATCH` 返回 fake-IP；`nameserver-policy` 与路由、fake-IP 同源，这两类走阿里 DoH 并直连。
- `gfwlist.yaml`：`private` 返回真实 IP，`gfw`（DustinWin `gfw.mrs`）返回 fake-IP，`MATCH`（其余域名）返回真实 IP；`gfw` 域名经“节点选择”走 Google DoH，其余域名走阿里 DoH。
- 代理节点域名使用阿里 DoH 做启动解析。
- 未使用 `fallback`、`fallback-filter`、`system` 或独立 geodata。

DNS 与连接路由分别判断。`core.yaml` 里国内域名直接放行，未分类域名解析到大陆 IP 后也直连，否则代理；`gfwlist.yaml` 里只有 `gfw` 域名交给节点，其余域名解析后直连。两档都不会为了试探国内 IP 而先把未分类域名发给国内 DNS，因此与 HomeProxy 的应答 IP 筛选不是完全相同的算法。

`respect-rules` 让 DNS 上游遵循路由；海外上游额外指定“节点选择”，避免出口随 IP 规则变化。不配置 `direct-nameserver`，避免根据一份解析结果判为大陆后，又重解析成另一目标地址。

客户端应接管 DNS，使用 fake-ip，保留模板的规则过滤和地址池，不用客户端旧配置覆盖。Nikki 的大陆 IPv4/IPv6 旁路分别开启后，真实目标 IP 命中对应集合即提前放行；fake-IP 连接进入内核。未收录域名即使后续解析到大陆 IP，也是在内核中直连，不是提前旁路。模板不会自动开启这些开关；验证 YAML 完整规则时应关闭旁路，让流量进入内核。IPv6 流量也需要接管；若客户端不支持，应同时关闭顶层 `ipv6` 和 `dns.ipv6`。

私有域名规则只决定出口；私有主机名能否解析仍取决于本地 DNS。需要解析家庭内网名称时，可自行为对应后缀指定实际内网 DNS，模板不假定网关地址。

配置加载和域名矩阵不等于实际 DNS、CDN 或代理连通性验证，部署后仍需在客户端检查。
