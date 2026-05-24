# Repository Guidelines

## Project Structure & Module Organization

This repository is a compact Mihomo configuration template project.

- `Full.yaml` is the full template and should remain node-free; it keeps AI, streaming, Google, Apple, Microsoft, developer tooling, gaming platform, and region node strategy groups.
- `Mini.yaml` is the daily-driver minimal template and should remain node-free; it keeps only `手动切换`, `自动测速`, `AI出口`, `流媒体`, and `漏网之鱼`.
- `scripts/convert.js` contains the JavaScript operator for creating chained proxy nodes from `relay` and `landing` arguments.
- `demo/` stores example Mihomo YAML files used for reference and manual comparison.
- `ruleset/` is reserved for external or generated rule-set assets if they are added later.
- `README.md` documents user-facing behavior and should be updated when routing logic or template selection changes.
- `LICENSE` covers this repository's own template and script content; remotely referenced icons, demo rules, and other third-party resources remain under their upstream terms.

## Build, Test, and Development Commands

There is no package manager manifest and no generated build step. Use lightweight validation before committing:

- `node --check scripts/convert.js` verifies JavaScript syntax without executing the operator.
- `mihomo -t -f Full.yaml` and `mihomo -t -f Mini.yaml` validate the templates when the Mihomo binary is installed locally.
- `yamllint Full.yaml Mini.yaml demo/*.yaml` checks YAML formatting when `yamllint` is available.
- `git diff --check` catches trailing whitespace and common patch formatting issues.

## Coding Style & Naming Conventions

Keep YAML indentation at two spaces and group rules by routing intent, with short comments explaining each block. Preserve established Chinese strategy-group names such as `手动切换`, `自动测速`, `漏网之鱼`, `AI出口`, `流媒体`, `谷歌服务`, `苹果服务`, `微软服务`, `开发工具`, and `游戏平台` unless a routing change requires renaming them. Keep `Mini.yaml` intentionally smaller than `Full.yaml`; do not add brand, developer, gaming, or region node groups there unless the template goal is explicitly changed. For overlapping `GEOSITE` categories, place the more specific or higher-intent rule first; for example, keep `GEOSITE,category-dev` before `GEOSITE,microsoft` so GitHub traffic reaches `开发工具`. Top-level scenario `select` groups should keep a consistent candidate order and use `include-all: true` so each scenario can directly select a concrete node without adding one-off duplicate groups such as `开发自建节点`. In JavaScript, use two-space indentation, semicolons, `const`/`let`, and small helper functions as shown in `scripts/convert.js`. Prefer descriptive argument aliases and avoid changing existing aliases unless backward compatibility is intentionally broken.

## Testing Guidelines

No automated test suite is currently checked in. For configuration edits, validate changed templates with Mihomo and manually compare behavior against `demo/` examples where relevant. For `scripts/convert.js`, run `node --check` and test the operator in the target subscription-conversion environment with both required arguments:

```text
relay=<中转节点名>&landing=<落地节点名>&name=<自定义名称>
```

## Commit & Pull Request Guidelines

Recent history mostly follows Conventional Commit style with optional scopes, for example `chore(rules): ...`, `feat(config): ...`, and `refactor(config): ...`. Use concise Chinese or English summaries, and choose scopes such as `config`, `rules`, `docs`, or `scripts`.

Pull requests should describe the routing or script behavior changed, list validation commands run, and mention compatibility risks for existing Mihomo clients. For template changes, state whether the change affects `Full.yaml`, `Mini.yaml`, or both. Include screenshots only when UI panel behavior or strategy-group ordering is relevant.

## Security & Configuration Tips

Do not commit personal proxy nodes, subscription URLs, credentials, API tokens, or generated configs containing private endpoints. Keep `Full.yaml` and `Mini.yaml` as reusable public templates. Do not vendor third-party icon assets or rulesets unless their license and attribution requirements are checked and documented; remote icon references currently point mainly to `Koolson/Qure` and `Orz-3/mini`.
