---
name: sift-route-debug
description: Diagnose Sift Mihomo routing decisions for RULE-SET and MetaCubeX GEOSITE/GEOIP templates under rules/. Use when investigating why a domain or IP is routed direct/proxy, when checking first-match rule attribution, or when adding route regression expectations.
---

# sift-route-debug

Use this skill when a Sift domain or IP route needs attribution: "why did this go direct?", "which rule matched?", "is this caused by cn-lite / GEOSITE,cn / GEOIP,CN?", or similar.

## Commands

```bash
.agents/skills/sift-route-debug/scripts/explain_route.py rules/DustinWin-full.yaml example.com
.agents/skills/sift-route-debug/scripts/explain_route.py rules/MetaCubeX-core.yaml play.googleapis.com
.agents/skills/sift-route-debug/scripts/update_cache.py rules/DustinWin-full.yaml
.agents/skills/sift-route-debug/scripts/update_cache.py rules/MetaCubeX-full.yaml
```

## Workflow

1. Run `explain_route.py <template> <domain-or-ip>`.
2. If it reports missing cached rules, run `update_cache.py <template>` and retry.
3. Treat the target YAML as the only source of truth:
   - DustinWin and ACL4SSR templates read `rule-providers.*.url` and `behavior`.
   - MetaCubeX templates read `geox-url.geosite`, `geox-url.geoip`, and `geox-url.mmdb`.
   - do not hardcode MetaCubeX or any other upstream in scripts or reasoning.
4. For domain input, MetaCubeX diagnosis defaults to GeoSite only and does not resolve DNS. Mention that runtime may later hit `GEOIP` after DNS resolution.
5. For IP input, diagnose IP providers or `GEOIP` rules only.
6. If a misroute is confirmed, suggest adding the domain/IP to route expectations once that checker exists.

## Reading Results

`explain_route.py` prints the first matching template rule in Mihomo rule order. For DustinWin and ACL4SSR templates it includes the provider name, provider source, behavior, and matched provider entry. For MetaCubeX templates it includes matched GeoSite/GeoIP tags from the configured geo database and the first matching `GEOSITE`/`GEOIP` rule.

Common Sift cases to call out:

- `proxy` is the explicit non-CN proxy layer in DustinWin templates (after service/brand rules, before `cn-lite`); `cn-lite`, `apple-cn`, `microsoft-cn`, and `games-cn` are direct-domain rules.
- `GEOSITE,cn` and `GEOIP,CN` are direct fallbacks in MetaCubeX templates.
- Core intentionally routes full Apple and Microsoft rules to `全球直连`.
- A domain that has no domain-rule match can still route by IP at runtime if DNS resolution produces an IP matched by an IP rule.
