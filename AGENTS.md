# Repository Guidelines

Sift 只维护 `rules/core.yaml`：Mihomo 无节点大陆白名单模板。用户文档以 README.md 为准。

## 产品合同

- 仅“节点选择”“自动测速”两个组；不恢复 Full/Core/Nano、品牌、地区、广告或兜底组。
- 私有域名/IP → DIRECT；cn-lite → DIRECT；cnip → DIRECT；MATCH → 节点选择。
- 不设置 Google Play 等服务专用代理例外，统一按白名单和 IP 判断。
- 使用 fake-ip 规则模式：private / cn-lite → real-ip，MATCH → fake-ip；保留映射持久化。国内白名单/私有域名走国内 DoH，其余需要真实解析时走代理海外 DoH。
- 不照搬 HomeProxy 的防火墙旁路、常用端口限制、QUIC 拒绝或 sing-box DNS 应答筛选。
- 不使用并发 fallback、system DNS、GeoIP 数据库；保持 RULE-SET、MRS、jsDelivr、provider 下载 DIRECT。
- 路由白名单保持 cn-lite，不随意换成宽 cn。
- 保留 include-all、信息节点 exclude-filter；测速 timeout 3000、expected-status 204、lazy true。
- 不提交节点、订阅、密钥或生成的私有配置。

## 目录

`rules/core.yaml` 为唯一 YAML；`demo/README.md` 只保留第三方参考链接。`docs/dns.md` 说明当前 DNS，其他 docs 为背景材料，按需读取。

## 修改与验证

YAML 两空格缩进，不写注释。行为变化同步 README.md、docs/dns.md 和路由矩阵。
使用 `.agents/skills/sift-route-debug/SKILL.md` 验证，运行：

```sh
python .agents/skills/sift-route-debug/scripts/check.py
```

域名矩阵不解析域名，无法证明运行时 IP 路由或 DNS 行为。IP 回归需使用明确 IP；实际部署连通性另行确认。

提交使用 Conventional Commits；说明行为变化、验证范围与客户端迁移影响。
