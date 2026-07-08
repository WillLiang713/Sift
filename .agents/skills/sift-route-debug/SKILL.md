---
name: sift-route-debug
description: Diagnose Sift Mihomo routing decisions for root RULE-SET templates and geodata GEOSITE/GEOIP templates. Use when investigating why a domain or IP is routed direct/proxy, when checking first-match rule attribution, or when adding route regression expectations.
---

# sift-route-debug

Use this skill when a Sift domain or IP route needs attribution: "why did this go direct?", "which rule matched?", "is this caused by cn-lite / GEOSITE,cn / GEOIP,CN?", or similar.

## Commands

```bash
.agents/skills/sift-route-debug/scripts/explain_route.py Full.yaml example.com
.agents/skills/sift-route-debug/scripts/explain_route.py geodata/Core.yaml play.googleapis.com
.agents/skills/sift-route-debug/scripts/update_cache.py Full.yaml
.agents/skills/sift-route-debug/scripts/update_cache.py geodata/Full.yaml
```

## Workflow

1. Run `explain_route.py <template> <domain-or-ip>`.
2. If it reports missing cached rules, run `update_cache.py <template>` and retry.
3. Treat the target YAML as the only source of truth:
   - root templates read `rule-providers.*.url` and `behavior`.
   - geodata templates read `geox-url.geosite`, `geox-url.geoip`, and `geox-url.mmdb`.
   - do not hardcode MetaCubeX or any other upstream in scripts or reasoning.
4. For domain input, geodata diagnosis defaults to GeoSite only and does not resolve DNS. Mention that runtime may later hit `GEOIP` after DNS resolution.
5. For IP input, diagnose IP providers or `GEOIP` rules only.
6. If a misroute is confirmed, suggest adding the domain/IP to route expectations once that checker exists.

## Reading Results

`explain_route.py` prints the first matching template rule in Mihomo rule order. For root templates it includes the provider name, provider source, behavior, and matched provider entry. For geodata templates it includes matched GeoSite/GeoIP tags from the configured geo database and the first matching `GEOSITE`/`GEOIP` rule.

Common Sift cases to call out:

- `cn-lite`, `google-cn`, `apple-cn`, `microsoft-cn`, and `games-cn` are early direct-domain rules in root templates.
- `GEOSITE,cn` and `GEOIP,CN` are direct fallbacks in geodata templates.
- Core intentionally routes full Apple and Microsoft rules to `全球直连`.
- A domain that has no domain-rule match can still route by IP at runtime if DNS resolution produces an IP matched by an IP rule.
