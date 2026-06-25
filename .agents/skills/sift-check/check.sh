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
FULL_REQ="节点选择 手动切换 自动测速 AI 流媒体 游戏平台 香港节点 美国节点 日本节点 新加坡节点 其他节点 全球直连 漏网之鱼"
FULL_FORB=""
NANO_REQ="节点选择 手动切换 自动测速 全球直连 漏网之鱼"
NANO_FORB="AI 流媒体 游戏平台 香港节点 美国节点 日本节点 新加坡节点 其他节点"

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
}
{ sub(/\r$/,"") }                                  # normalize CRLF

/^[A-Za-z][A-Za-z0-9_-]*:/ {                       # top-level mapping key (col 0)
  key=$0; sub(/:.*/,"",key)
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
  if($0 ~ /^    url:/){ u=$0; sub(/^    url:[ \t]*/,"",u); gsub(/"/,"",u); u=trim(u); url_key[nurl]=pk; url_val[nurl]=u; nurl++; next }
  next
}

section=="rules" {
  if($0 ~ /^- /){
    r=$0; sub(/^- /,"",r); r=trim(r)
    m=split(r, f, ","); for(j=1;j<=m;j++) f[j]=trim(f[j])
    pi=m; if(f[m]=="no-resolve" || f[m]=="src") pi=m-1
    if(f[pi]!=""){ pols[npol]=f[pi]; npol++ }
    if(f[1]=="RULE-SET" && m>=2){ rsrefs[nrs]=f[2]; nrs++ }
    next
  }
  next
}

section=="dns" {                                   # dns block: collect fake-ip-filter rule-set refs
  if($0 ~ /^[ \t]*-[ \t]*rule-set:/){
    s=$0; sub(/.*rule-set:[ \t]*/,"",s); sub(/[ \t,].*$/,"",s); gsub(/["']/,"",s); s=trim(s)
    if(s!=""){ dnsrs[ndnsrs]=s; ndnsrs++ }
  }
  next
}

END{
  if(fail_proxies) emit("FAIL","top-level `proxies:` present — template must stay node-free")
  if(fail_dns)     emit("FAIL","top-level `dns:`/`fake-ip` present — this template must stay DNS-free")

  for(i=0;i<np;i++){ r=pf_r[i]; if(!(r in groups) && !(r in builtin)) emit("FAIL","group `" pf_g[i] "` references undefined proxy `" r "`") }
  for(i=0;i<npol;i++){ p=pols[i]; if(!(p in groups) && !(p in builtin)) emit("FAIL","rule policy `" p "` is not a defined group or builtin") }
  for(i=0;i<nrs;i++){ s=rsrefs[i]; usedprov[s]=1; if(!(s in provs)) emit("FAIL","RULE-SET references undefined provider `" s "`") }
  for(i=0;i<ndnsrs;i++){ s=dnsrs[i]; usedprov[s]=1; if(!(s in provs)) emit("FAIL","fake-ip-filter references undefined provider `" s "`") }
  for(k in provs) if(!(k in usedprov)) emit("WARN","rule-provider `" k "` defined but never used in rules")

  for(i=0;i<nurl;i++){
    u=url_val[i]; lu=tolower(u)
    if(lu ~ /geoip|geosite/) emit("FAIL","provider `" url_key[i] "` URL contains geoip/geosite — triggers ShellCrash geo misdetection: " u)
    else if(lu !~ /dustinwin/) emit("WARN","provider `" url_key[i] "` URL is not a DustinWin source — verify it is keyword-free and attribution is documented: " u)
    nn=split(u, pp, "/"); base=pp[nn]; sub(/\.mrs.*$/,"",base)
    if(base!="" && base!=url_key[i]) emit("INFO","provider key `" url_key[i] "` maps to file `" base "` (basename != key; OK if intentional, see AGENTS.md)")
  }

  for(k in reqset)  if(!(k in groups)) emit("FAIL","required strategy group `" k "` is missing")
  for(k in forbset) if(k in groups)    emit("FAIL","group `" k "` must not exist in this template (Nano scope creep)")
}
AWKEOF
)

fails=0; warns=0

check_file(){
  local file="$1" role="$2" req="$3" forb="$4" allow_dns="$5"
  printf '\n== %s (%s) ==\n' "$file" "$role"
  if [ ! -f "$file" ]; then printf '  [SKIP] not found\n'; return; fi
  local out before="$fails"
  out=$(awk -v required="$req" -v forbidden="$forb" -v allow_dns="$allow_dns" "$AWK" "$file")
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

check_file Full.yaml full "$FULL_REQ" "$FULL_FORB" 1
check_file Nano.yaml nano "$NANO_REQ" "$NANO_FORB" 0

# --- Optional toolchain -------------------------------------------------------
printf '\n== toolchain ==\n'
if command -v mihomo >/dev/null 2>&1; then
  for f in Full.yaml Nano.yaml; do
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
  if yamllint -d relaxed Full.yaml Nano.yaml >"$tmp" 2>&1; then printf '  [ OK ] yamllint\n'
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
