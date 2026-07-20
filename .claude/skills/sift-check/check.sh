#!/usr/bin/env bash
# sift-check — validate the Sift Mihomo templates against project invariants.
# Pure bash + awk. Optional: mihomo / yamllint / git (used only if present).
# Exit 0 = PASS (no failures), 1 = at least one [FAIL].
set -u

# Run from the repo root so relative template paths resolve.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT" || exit 2

# --- Canonical contract -------------------------------------------------------
# Keep these in sync with AGENTS.md when a strategy group is added/renamed/removed.
FULL_REQ="节点选择 手动切换 自动测速 AI 流媒体 游戏平台 Telegram 苹果服务 谷歌服务 微软服务 OneDrive 香港节点 美国节点 日本节点 新加坡节点 其他节点 全球直连 广告拦截 漏网之鱼"
FULL_FORB=""
CORE_REQ="节点选择 手动切换 自动测速 全球直连 广告拦截"
CORE_FORB="AI 流媒体 游戏平台 Telegram 苹果服务 谷歌服务 微软服务 OneDrive 香港节点 美国节点 日本节点 新加坡节点 其他节点 漏网之鱼"
NANO_REQ="节点选择 手动切换 自动测速 全球直连 广告拦截 漏网之鱼"
NANO_FORB="AI 流媒体 游戏平台 Telegram 苹果服务 谷歌服务 微软服务 OneDrive 香港节点 美国节点 日本节点 新加坡节点 其他节点"
# Geodata templates keep the same group contracts and route with GEOSITE/GEOIP.
# Allowed DNS-only providers: fakeip-filter and trackerslist (domestic DNS uses geosite:cn / geosite:private).

# --- Static analyzer (one pass per file) --------------------------------------
AWK=$(cat <<'AWKEOF'
function trim(s){ sub(/^[ \t]+/,"",s); sub(/[ \t]+$/,"",s); return s }
function emit(lvl,msg){ printf "%s\t%s\n", lvl, msg }
BEGIN{
  split("DIRECT REJECT REJECT-DROP PASS COMPATIBLE GLOBAL", bi, " ")
  for(i in bi) builtin[bi[i]]=1
  split(required, rq, " ");  for(i in rq) if(rq[i]!="") reqset[rq[i]]=1
  split(forbidden, fb, " "); for(i in fb) if(fb[i]!="") forbset[fb[i]]=1
  section=""; g=""; in_proxies=0; pk=""
  np=0; npol=0; nrs=0; nurl=0; ndnsrs=0
  top_ipv6_true=0; dns_ipv6_true=0
}
{ sub(/\r$/,"") }                                  # normalize CRLF

/^[A-Za-z][A-Za-z0-9_-]*:/ {                       # top-level mapping key (col 0)
  key=$0; sub(/:.*/,"",key)
  if(key=="ipv6"){
    v=$0; sub(/^[^:]*:[ \t]*/,"",v); v=trim(v)
    if(v=="true") top_ipv6_true=1
  }
  if(key=="proxy-groups")        section="pg"
  else if(key=="rule-providers") section="rp"
  else if(key=="rules")          section="rules"
  else if(key=="dns")            section="dns"
  else                           section="other"
  if(key=="proxies") fail_proxies=1
  if((key=="dns" || key=="fake-ip") && allow_dns!="1") fail_dns=1
  in_proxies=0; next
}

section=="pg" {
  if($0 ~ /^- name:/){ n=$0; sub(/^- name:[ \t]*/,"",n); n=trim(n); g=n; groups[n]=1; in_proxies=0; next }
  if($0 ~ /^  proxies:[ \t]*$/){ in_proxies=1; next }
  if($0 ~ /^  [A-Za-z]/){ in_proxies=0; next }      # any other group key ends the proxies list
  if(in_proxies && $0 ~ /^  - /){ r=$0; sub(/^  - /,"",r); r=trim(r); if(r!=""){ pf_g[np]=g; pf_r[np]=r; np++ } next }
  next
}

section=="rp" {
  if($0 ~ /^  [A-Za-z0-9_-]+:[ \t]*$/){ pk=$0; sub(/^  /,"",pk); sub(/:.*/,"",pk); pk=trim(pk); provs[pk]=1; next }
  if($0 ~ /^    behavior:/){ b=$0; sub(/^    behavior:[ \t]*/,"",b); gsub(/"/,"",b); b=trim(b); prov_behavior[pk]=b; next }
  if($0 ~ /^    url:/){ u=$0; sub(/^    url:[ \t]*/,"",u); gsub(/"/,"",u); u=trim(u); url_key[nurl]=pk; url_val[nurl]=u; nurl++; next }
  next
}

section=="rules" {
  if($0 ~ /^- /){
    r=$0; sub(/^- /,"",r); r=trim(r)
    m=split(r, f, ","); for(j=1;j<=m;j++) f[j]=trim(f[j])
    pi=m; if(f[m]=="no-resolve" || f[m]=="src") pi=m-1
    if(f[pi]!=""){ pols[npol]=f[pi]; npol++ }
    if(f[1]=="RULE-SET" && m>=2){
      if(geodata=="1") emit("FAIL","Geodata template must use GEOSITE/GEOIP, not RULE-SET: " r)
      rsrefs[nrs]=f[2]; nrs++
    }
    next
  }
  next
}

section=="dns" {                                   # dns block: collect rule-set refs
  if($0 ~ /^  ipv6:[ \t]*true([ \t]*#.*)?$/) dns_ipv6_true=1
  s=$0; sub(/#.*/,"",s)
  # Support "rule-set:a,private" / multi rule-set tokens on one policy key
  while(match(s, /rule-set:[ \t]*[A-Za-z0-9_-]+/)){
    t=substr(s, RSTART, RLENGTH); sub(/^rule-set:[ \t]*/,"",t); t=trim(t)
    if(t!="" && !(t in dnsseen)){ dnsseen[t]=1; dnsrs[ndnsrs]=t; ndnsrs++ }
    s=substr(s, RSTART+RLENGTH)
  }
  next
}

END{
  if(fail_proxies)    emit("FAIL","top-level `proxies:` present — template must stay node-free")
  if(fail_dns)        emit("FAIL","top-level `dns:`/`fake-ip` present — this template must stay DNS-free")
  if(allow_dns=="1" && !top_ipv6_true) emit("FAIL","DNS template must set top-level `ipv6: true` to allow IPv6 connections")
  if(allow_dns=="1" && !dns_ipv6_true) emit("FAIL","DNS template must set `dns.ipv6: true` to return AAAA answers")
  if(geodata=="1") for(k in provs)
    if(k!="fakeip-filter" && k!="trackerslist")
      emit("FAIL","Geodata template may only define DNS-only providers `fakeip-filter` / `trackerslist`, not `" k "`")

  for(i=0;i<np;i++){ r=pf_r[i]; if(!(r in groups) && !(r in builtin)) emit("FAIL","group `" pf_g[i] "` references undefined proxy `" r "`") }
  for(i=0;i<npol;i++){ p=pols[i]; if(!(p in groups) && !(p in builtin)) emit("FAIL","rule policy `" p "` is not a defined group or builtin") }
  for(i=0;i<nrs;i++){ s=rsrefs[i]; usedprov[s]=1; if(!(s in provs)) emit("FAIL","RULE-SET references undefined provider `" s "`") }
  for(i=0;i<ndnsrs;i++){
    s=dnsrs[i]; usedprov[s]=1
    if(!(s in provs)) emit("FAIL","DNS rule-set references undefined provider `" s "`")
    else if(prov_behavior[s]!="domain")
      emit("FAIL","DNS rule-set `" s "` uses behavior `" prov_behavior[s] "` — use domain-only providers in fake-ip-filter/nameserver-policy")
  }
  for(k in provs) if(!(k in usedprov)) emit("WARN","rule-provider `" k "` defined but never used in rules")

  for(i=0;i<nurl;i++){
    u=url_val[i]
    # ShellCrash geo-keyword URL heuristics are intentionally not enforced here.
    nn=split(u, pp, "/"); base=pp[nn]; sub(/\.(mrs|list).*$/,"",base)
    if(base!="" && base!=url_key[i]) emit("INFO","provider key `" url_key[i] "` maps to file `" base "` (basename != key; OK if intentional, see AGENTS.md)")
  }

  for(k in reqset)  if(!(k in groups)) emit("FAIL","required strategy group `" k "` is missing")
  for(k in forbset) if(k in groups)    emit("FAIL","group `" k "` must not exist in this template (Nano scope creep)")
}
AWKEOF
)

fails=0; warns=0

check_file(){
  local file="$1" role="$2" req="$3" forb="$4" allow_dns="$5" geodata="${6:-0}"
  printf '\n== %s (%s) ==\n' "$file" "$role"
  if [ ! -f "$file" ]; then printf '  [SKIP] not found\n'; return; fi
  local out before="$fails"
  out=$(awk -v required="$req" -v forbidden="$forb" -v allow_dns="$allow_dns" -v geodata="$geodata" "$AWK" "$file")
  if [ -z "$out" ]; then printf '  [ OK ] all structural invariants passed\n'; return; fi
  while IFS=$'\t' read -r lvl msg; do
    [ -z "$lvl" ] && continue
    case "$lvl" in
      FAIL) printf '  [FAIL] %s\n' "$msg"; fails=$((fails+1));;
      WARN) printf '  [WARN] %s\n' "$msg"; warns=$((warns+1));;
      INFO) printf '  [INFO] %s\n' "$msg";;
      *)    printf '  [%s] %s\n' "$lvl" "$msg";;
    esac
  done <<< "$out"
  [ "$fails" -eq "$before" ] && printf '  [ OK ] no structural failures\n'
}

TEMPLATES=(
  rules/DustinWin-full.yaml
  rules/DustinWin-core.yaml
  rules/DustinWin-nano.yaml
  rules/MetaCubeX-full.yaml
  rules/MetaCubeX-core.yaml
  rules/MetaCubeX-nano.yaml
  rules/ACL4SSR-full.yaml
  rules/ACL4SSR-core.yaml
  rules/ACL4SSR-nano.yaml
)

check_file rules/DustinWin-full.yaml DustinWin-full "$FULL_REQ" "$FULL_FORB" 1 0
check_file rules/DustinWin-core.yaml DustinWin-core "$CORE_REQ" "$CORE_FORB" 1 0
check_file rules/DustinWin-nano.yaml DustinWin-nano "$NANO_REQ" "$NANO_FORB" 0 0
check_file rules/MetaCubeX-full.yaml MetaCubeX-full "$FULL_REQ" "$FULL_FORB" 1 1
check_file rules/MetaCubeX-core.yaml MetaCubeX-core "$CORE_REQ" "$CORE_FORB" 1 1
check_file rules/MetaCubeX-nano.yaml MetaCubeX-nano "$NANO_REQ" "$NANO_FORB" 0 1
check_file rules/ACL4SSR-full.yaml ACL4SSR-full "$FULL_REQ" "$FULL_FORB" 1 0
check_file rules/ACL4SSR-core.yaml ACL4SSR-core "$CORE_REQ" "$CORE_FORB" 1 0
check_file rules/ACL4SSR-nano.yaml ACL4SSR-nano "$NANO_REQ" "$NANO_FORB" 0 0

# Full/Core Tracker domains are DNS compatibility exceptions only: return real-IP,
# but do not force DIRECT / 全球直连 or any other routing policy.
for f in \
  rules/DustinWin-full.yaml rules/DustinWin-core.yaml \
  rules/MetaCubeX-full.yaml rules/MetaCubeX-core.yaml \
  rules/ACL4SSR-full.yaml rules/ACL4SSR-core.yaml; do
  dns_tracker=$(awk '
    /^dns:$/ { in_dns=1; next }
    in_dns && /^[A-Za-z][A-Za-z0-9_-]*:/ { in_dns=0 }
    in_dns && $0 ~ /^    - rule-set:trackerslist([[:space:]]*#.*)?$/ { print NR; exit }
  ' "$f")
  route_tracker=$(awk '/^- RULE-SET,trackerslist,/{ print NR; exit }' "$f")
  if [ -z "$dns_tracker" ]; then
    printf '  [FAIL] %s must reference trackerslist from dns.fake-ip-filter\n' "$f"
    fails=$((fails+1))
  elif [ -n "$route_tracker" ]; then
    printf '  [FAIL] %s must not route trackerslist; it is DNS-only real-IP\n' "$f"
    fails=$((fails+1))
  else
    printf '  [ OK ] %s keeps trackerslist DNS-only real-IP\n' "$f"
  fi
done

# DustinWin proxy (geolocation-!cn + gfwlist) covers global .cn exceptions such as
# googleapis.cn. It must take precedence over cn-lite's broad +.cn entry, matching
# MetaCubeX geolocation-!cn / ACL4SSR ProxyLite placement.
for f in rules/DustinWin-full.yaml rules/DustinWin-core.yaml rules/DustinWin-nano.yaml; do
  proxy_line=$(awk '/^- RULE-SET,proxy,节点选择/{ print NR; exit }' "$f")
  cn_line=$(awk '/^- RULE-SET,cn-lite,全球直连/{ print NR; exit }' "$f")
  if [ -z "$proxy_line" ] || [ -z "$cn_line" ]; then
    printf '  [FAIL] %s must route proxy and cn-lite\n' "$f"
    fails=$((fails+1))
  elif [ "$proxy_line" -lt "$cn_line" ]; then
    printf '  [ OK ] %s routes proxy before cn-lite\n' "$f"
  else
    printf '  [FAIL] %s must route proxy before cn-lite\n' "$f"
    fails=$((fails+1))
  fi
done

# ACL4SSR ChinaDomain contains DOMAIN-SUFFIX,cn. ProxyLite must take precedence
# so googleapis.cn and other explicit proxy exceptions are not sent direct.
for f in rules/ACL4SSR-full.yaml rules/ACL4SSR-core.yaml rules/ACL4SSR-nano.yaml; do
  proxy_line=$(awk '/^- RULE-SET,ProxyLite,节点选择/{ print NR; exit }' "$f")
  china_line=$(awk '/^- RULE-SET,ChinaDomain,全球直连/{ print NR; exit }' "$f")
  if [ -z "$proxy_line" ] || [ -z "$china_line" ]; then
    printf '  [FAIL] %s must route ProxyLite and ChinaDomain\n' "$f"
    fails=$((fails+1))
  elif [ "$proxy_line" -lt "$china_line" ]; then
    printf '  [ OK ] %s routes ProxyLite before ChinaDomain\n' "$f"
  else
    printf '  [FAIL] %s must route ProxyLite before ChinaDomain\n' "$f"
    fails=$((fails+1))
  fi
  if grep -q '^- GEOIP,CN,' "$f"; then
    printf '  [FAIL] %s must use ChinaIp/ChinaIpV6 without trailing GEOIP,CN\n' "$f"
    fails=$((fails+1))
  else
    printf '  [ OK ] %s has no trailing GEOIP,CN fallback\n' "$f"
  fi
done

# MetaCubeX geolocation-!cn must precede cn. Google routing covers googleapis.cn /
# gstatic.cn (in cn/tld-cn but not geolocation-!cn):
# - Full: GEOSITE,google,谷歌服务 before geolocation-!cn and cn (UI strategy group)
# - Core/Nano: GEOSITE,google,节点选择 between geolocation-!cn and cn (routing-only)
for f in rules/MetaCubeX-full.yaml rules/MetaCubeX-core.yaml rules/MetaCubeX-nano.yaml; do
  noncn_line=$(awk '/^- GEOSITE,geolocation-!cn,节点选择/{ print NR; exit }' "$f")
  cn_line=$(awk '/^- GEOSITE,cn,全球直连/{ print NR; exit }' "$f")
  if [ -z "$noncn_line" ] || [ -z "$cn_line" ]; then
    printf '  [FAIL] %s must route geolocation-!cn and cn\n' "$f"
    fails=$((fails+1))
  elif [ "$noncn_line" -lt "$cn_line" ]; then
    printf '  [ OK ] %s routes geolocation-!cn before cn\n' "$f"
  else
    printf '  [FAIL] %s must route geolocation-!cn before cn\n' "$f"
    fails=$((fails+1))
  fi
  case "$f" in
    *MetaCubeX-full.yaml)
      google_line=$(awk '/^- GEOSITE,google,谷歌服务/{ print NR; exit }' "$f")
      if [ -z "$google_line" ] || [ -z "$cn_line" ] || [ -z "$noncn_line" ]; then
        printf '  [FAIL] %s must route GEOSITE,google,谷歌服务 before cn\n' "$f"
        fails=$((fails+1))
      elif [ "$google_line" -lt "$noncn_line" ] && [ "$google_line" -lt "$cn_line" ]; then
        printf '  [ OK ] %s routes google (谷歌服务) before geolocation-!cn and cn\n' "$f"
      else
        printf '  [FAIL] %s must route google (谷歌服务) before geolocation-!cn and cn\n' "$f"
        fails=$((fails+1))
      fi
      ;;
    *)
      google_line=$(awk '/^- GEOSITE,google,节点选择/{ print NR; exit }' "$f")
      if [ -z "$google_line" ]; then
        printf '  [FAIL] %s must route google before cn (googleapis.cn exception)\n' "$f"
        fails=$((fails+1))
      elif [ -n "$noncn_line" ] && [ -n "$cn_line" ] \
        && [ "$noncn_line" -lt "$google_line" ] && [ "$google_line" -lt "$cn_line" ]; then
        printf '  [ OK ] %s routes google between geolocation-!cn and cn\n' "$f"
      else
        printf '  [FAIL] %s must route google between geolocation-!cn and cn\n' "$f"
        fails=$((fails+1))
      fi
      ;;
  esac
done

# --- Optional toolchain -------------------------------------------------------
printf '\n== toolchain ==\n'
if command -v mihomo >/dev/null 2>&1; then
  for f in "${TEMPLATES[@]}"; do
    [ -f "$f" ] || continue
    tmp=$(mktemp)
    if mihomo -t -f "$f" >"$tmp" 2>&1; then printf '  [ OK ] mihomo -t %s\n' "$f"
    else printf '  [FAIL] mihomo -t %s\n' "$f"; sed 's/^/         /' "$tmp"; fails=$((fails+1)); fi
    rm -f "$tmp"
  done
else
  printf '  [SKIP] mihomo not on PATH (install to enable full config validation)\n'
fi

if command -v yamllint >/dev/null 2>&1; then
  tmp=$(mktemp)
  if yamllint -d relaxed "${TEMPLATES[@]}" >"$tmp" 2>&1; then printf '  [ OK ] yamllint\n'
  else printf '  [WARN] yamllint findings:\n'; sed 's/^/         /' "$tmp"; warns=$((warns+1)); fi
  rm -f "$tmp"
else
  printf '  [SKIP] yamllint not on PATH\n'
fi

if git rev-parse --git-dir >/dev/null 2>&1; then
  if git diff --check >/dev/null 2>&1; then printf '  [ OK ] git diff --check (no whitespace errors)\n'
  else printf '  [WARN] git diff --check found whitespace issues\n'; warns=$((warns+1)); fi
fi

# --- Summary ------------------------------------------------------------------
printf '\n== summary ==\n  %d failure(s), %d warning(s)\n' "$fails" "$warns"
if [ "$fails" -eq 0 ]; then printf '  PASS\n'; exit 0; else printf '  FAIL\n'; exit 1; fi
