---
name: sift-route-debug
description: Validate the Sift whitelist template with pinned Mihomo and diagnose domain/IP routes.
---

# Sift route checks

模板为 `rules/core.yaml`（矩阵标签 `Sift`）与 `rules/gfwlist.yaml`（矩阵标签 `Sift-GFW`）。

```sh
python .agents/skills/sift-route-debug/scripts/check.py
python .agents/skills/sift-route-debug/scripts/check.py --quick
python .agents/skills/sift-route-debug/scripts/explain_route.py rules/core.yaml googleapis.cn
python .agents/skills/sift-route-debug/scripts/explain_route.py rules/core.yaml 223.5.5.5
```

完整检查使用固定版本 Mihomo 原生加载、刷新模板声明的 MRS 缓存、执行路由矩阵并检查 git diff。缓存位于 `.cache/`，不提交。

变更路由时同步 `matrix_route.py` 的 `default_expectations()`。规则与来源以 YAML 为准，不硬编码其他来源。

合同：两档都是私有域名/IP 直连、无服务专用例外；`Sift` 国内域名和大陆 IP 直连、其余代理；`Sift-GFW` 只有 `gfw` 域名代理、其余直连。

域名诊断不做 DNS 查询，会跳过 IP 规则；未收录域名在运行时可能因解析到大陆 IP 而直连。明确 IP 输入用于验证 IP 集。矩阵不能证明 DNS 上游出口、真实应答或节点可用性；部署验证单独执行。
