# DNS 设计

当前唯一模板为 [core.yaml](../rules/core.yaml)。

- `fake-ip` 使用规则过滤：`private`、`cn` 返回真实 IP，`MATCH` 返回 fake-IP。
- IPv4 fake-IP 地址池为 `198.18.0.1/16`，开启映射持久化。
- `nameserver-policy` 与路由、fake-IP 白名单同源：`private` / 全量 `cn`（DustinWin `cn.mrs`，不用 `cn-lite`）走阿里 DoH 并直连。
- 其他域名先返回 fake-IP；需要真实解析时使用 Google DoH，通过“节点选择”访问。
- 代理节点域名使用阿里 DoH 做启动解析。
- 未使用 `fallback`、`fallback-filter`、`system` 或独立 geodata。

DNS 与连接路由分别判断：国内域名直接放行；未分类域名解析到大陆 IP 后也直连，否则代理。未分类域名不会为了试探国内 IP 而先发给国内 DNS，因此与 HomeProxy 的应答 IP 筛选不是完全相同的算法。

`respect-rules` 让 DNS 上游遵循路由；海外上游额外指定“节点选择”，避免出口随 IP 规则变化。不配置 `direct-nameserver`，避免根据一份解析结果判为大陆后，又重解析成另一目标地址。

客户端应接管 DNS，使用 fake-ip，保留模板的规则过滤和地址池，不用客户端旧配置覆盖。Nikki 的大陆 IPv4/IPv6 旁路分别开启后，真实目标 IP 命中对应集合即提前放行；fake-IP 连接进入内核。未收录域名即使后续解析到大陆 IP，也是在内核中直连，不是提前旁路。模板不会自动开启这些开关；验证 YAML 完整规则时应关闭旁路，让流量进入内核。IPv6 流量也需要接管；若客户端不支持，应同时关闭顶层 `ipv6` 和 `dns.ipv6`。

私有域名规则只决定出口；私有主机名能否解析仍取决于本地 DNS。需要解析家庭内网名称时，可自行为对应后缀指定实际内网 DNS，模板不假定网关地址。

配置加载和域名矩阵不等于实际 DNS、CDN 或代理连通性验证，部署后仍需在客户端检查。
