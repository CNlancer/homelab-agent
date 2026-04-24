#!/bin/zsh
set -euo pipefail

TARGET_CONF='/Users/lancer/Library/Application Support/Surge/Profiles/PaoluzX.conf'
SURGE_DIR="${TARGET_CONF:h}"
HK_CONF="${SURGE_DIR}/PaoluzX-HK.conf"
TW_CONF="${SURGE_DIR}/PaoluzX-TW.conf"
HK_TW_CONF="${SURGE_DIR}/PaoluzX-HK+TW.conf"
OPS_LOG='/Users/lancer/projects/homelab-agent/var/ops-log.jsonl'

UPDATE_DERIVED='yes'
SCRIPT_NAME="${0:t}"

usage() {
  echo "Usage: $SCRIPT_NAME <subscription-link> [--update-derived=yes|no]" >&2
  echo "Example: $SCRIPT_NAME 'https://example.com/sub?token=***&subType=surge'" >&2
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

SUB_LINK="$1"
shift || true

for arg in "$@"; do
  case "$arg" in
    --update-derived=yes)
      UPDATE_DERIVED='yes'
      ;;
    --update-derived=no)
      UPDATE_DERIVED='no'
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ ! -d "${TARGET_CONF:h}" ]]; then
  echo "Target directory not found: ${TARGET_CONF:h}" >&2
  exit 1
fi

TMP_RAW="$(mktemp '/tmp/PaoluzX.raw.XXXXXX')"
TMP_FILTER="$(mktemp '/tmp/PaoluzX.filter.XXXXXX')"
trap 'rm -f "$TMP_RAW" "$TMP_FILTER"' EXIT

/usr/bin/curl -fsSL --connect-timeout 15 --max-time 120 "$SUB_LINK" -o "$TMP_RAW"

if ! /usr/bin/grep -q '^\[Proxy\]' "$TMP_RAW"; then
  echo "Downloaded content is not a valid Surge profile ([Proxy] missing)." >&2
  exit 1
fi

MAIN_BACKUP="${TARGET_CONF}.bak.$(/bin/date +%Y%m%d-%H%M%S)"
/bin/cp -p "$TARGET_CONF" "$MAIN_BACKUP"
/bin/mv "$TMP_RAW" "$TARGET_CONF"
TMP_RAW=''

filter_profile() {
  local mode="$1"
  local src="$2"
  local out="$3"
  local out_tmp
  local out_backup

  out_tmp="$(mktemp '/tmp/PaoluzX.derived.XXXXXX')"

  /usr/bin/awk -v mode="$mode" '
function trim(s) {
  sub(/^[ \t\r\n]+/, "", s)
  sub(/[ \t\r\n]+$/, "", s)
  return s
}

function proxy_name(line, parts) {
  split(line, parts, "=")
  return trim(parts[1])
}

function is_hk_name(name, lower) {
  lower = tolower(name)
  return (name ~ /香港/ || lower ~ /(^|[^[:alpha:]])hk([^[:alpha:]]|$)/ || lower ~ /hong[ -]?kong/)
}

function is_tw_name(name, lower) {
  lower = tolower(name)
  return (name ~ /台湾/ || lower ~ /(^|[^[:alpha:]])tw([^[:alpha:]]|$)/ || lower ~ /taiwan/)
}

function is_target_name(name) {
  if (mode == "HK") {
    return is_hk_name(name)
  }
  if (mode == "TW") {
    return is_tw_name(name)
  }
  if (mode == "HK_TW") {
    return (is_hk_name(name) || is_tw_name(name))
  }
  return 0
}

function add_csv(value, item) {
  item = trim(value)
  if (item == "") {
    return
  }
  if (csv == "") {
    csv = item
  } else {
    csv = csv ", " item
  }
}

function filter_group(line, pos, lhs, rhs, n, parts, cmd, i, item, options, filtered) {
  pos = index(line, "=")
  if (pos == 0) {
    print line
    return
  }

  lhs = trim(substr(line, 1, pos - 1))
  rhs = trim(substr(line, pos + 1))
  n = split(rhs, parts, ",")
  cmd = trim(parts[1])
  csv = ""
  options = ""

  if (cmd == "select") {
    for (i = 2; i <= n; i++) {
      item = trim(parts[i])
      if (item == "auto" || keep[item]) {
        add_csv(item)
      }
    }
    if (csv == "") {
      csv = first_keep
    }
    print lhs " = " cmd ", " csv
    return
  }

  if (cmd == "url-test" || cmd == "fallback" || cmd == "load-balance") {
    for (i = 2; i <= n; i++) {
      item = trim(parts[i])
      if (item ~ /^[A-Za-z0-9_-]+=/) {
        if (options == "") {
          options = item
        } else {
          options = options ", " item
        }
      } else if (keep[item]) {
        add_csv(item)
      }
    }
    if (csv == "") {
      csv = first_keep
    }
    filtered = lhs " = " cmd ", " csv
    if (options != "") {
      filtered = filtered ", " options
    }
    print filtered
    return
  }

  print line
}

FNR == NR {
  line = $0
  sub(/\r$/, "", line)
  if (line ~ /^\[/) {
    section = line
  }
  if (section == "[Proxy]" && line !~ /^[ \t]*(#|$)/ && index(line, "=") > 0) {
    name = proxy_name(line)
    if (is_target_name(name)) {
      keep[name] = 1
      if (first_keep == "") {
        first_keep = name
      }
    }
  }
  next
}

FNR != NR {
  line = $0
  sub(/\r$/, "", line)
  if (line ~ /^\[/) {
    section = line
    print line
    next
  }

  if (section == "[Proxy]") {
    if (line ~ /^[ \t]*(#|$)/) {
      print line
      next
    }
    name = proxy_name(line)
    if (keep[name]) {
      print line
    }
    next
  }

  if (section == "[Proxy Group]" && line !~ /^[ \t]*(#|$)/) {
    filter_group(line)
    next
  }

  print line
}
' "$src" "$src" > "$out_tmp"

  if ! /usr/bin/grep -q '^\[Proxy\]' "$out_tmp"; then
    echo "Generated profile missing [Proxy] for mode $mode: $out" >&2
    rm -f "$out_tmp"
    exit 1
  fi

  case "$mode" in
    HK)
      /usr/bin/awk '
function trim(s){sub(/^[ \t\r\n]+/,"",s);sub(/[ \t\r\n]+$/,"",s);return s}
function proxy_name(line,parts){split(line,parts,"=");return trim(parts[1])}
function is_hk_name(name,lower){lower=tolower(name);return (name~/香港/||lower~/(^|[^[:alpha:]])hk([^[:alpha:]]|$)/||lower~/hong[ -]?kong/)}
{
  line=$0; sub(/\r$/, "", line)
  if (line ~ /^\[/) section=line
  else if (section=="[Proxy]" && line !~ /^[ \t]*(#|$)/ && index(line,"=")>0) {
    name=proxy_name(line)
    if (!is_hk_name(name)) bad=1
    found=1
  }
}
END{ if (!found) exit 2; exit bad }
' "$out_tmp" > /dev/null
      ;;
    TW)
      /usr/bin/awk '
function trim(s){sub(/^[ \t\r\n]+/,"",s);sub(/[ \t\r\n]+$/,"",s);return s}
function proxy_name(line,parts){split(line,parts,"=");return trim(parts[1])}
function is_tw_name(name,lower){lower=tolower(name);return (name~/台湾/||lower~/(^|[^[:alpha:]])tw([^[:alpha:]]|$)/||lower~/taiwan/)}
{
  line=$0; sub(/\r$/, "", line)
  if (line ~ /^\[/) section=line
  else if (section=="[Proxy]" && line !~ /^[ \t]*(#|$)/ && index(line,"=")>0) {
    name=proxy_name(line)
    if (!is_tw_name(name)) bad=1
    found=1
  }
}
END{ if (!found) exit 2; exit bad }
' "$out_tmp" > /dev/null
      ;;
    HK_TW)
      /usr/bin/awk '
function trim(s){sub(/^[ \t\r\n]+/,"",s);sub(/[ \t\r\n]+$/,"",s);return s}
function proxy_name(line,parts){split(line,parts,"=");return trim(parts[1])}
function is_hk_name(name,lower){lower=tolower(name);return (name~/香港/||lower~/(^|[^[:alpha:]])hk([^[:alpha:]]|$)/||lower~/hong[ -]?kong/)}
function is_tw_name(name,lower){lower=tolower(name);return (name~/台湾/||lower~/(^|[^[:alpha:]])tw([^[:alpha:]]|$)/||lower~/taiwan/)}
{
  line=$0; sub(/\r$/, "", line)
  if (line ~ /^\[/) section=line
  else if (section=="[Proxy]" && line !~ /^[ \t]*(#|$)/ && index(line,"=")>0) {
    name=proxy_name(line)
    if (!(is_hk_name(name) || is_tw_name(name))) bad=1
    found=1
  }
}
END{ if (!found) exit 2; exit bad }
' "$out_tmp" > /dev/null
      ;;
  esac

  if [[ -f "$out" ]]; then
    out_backup="${out}.bak.$(/bin/date +%Y%m%d-%H%M%S)"
    /bin/cp -p "$out" "$out_backup"
  else
    out_backup=''
  fi

  /bin/mv "$out_tmp" "$out"
  echo "$out_backup"
}

HK_BACKUP=''
TW_BACKUP=''
HK_TW_BACKUP=''

if [[ "$UPDATE_DERIVED" == 'yes' ]]; then
  HK_BACKUP="$(filter_profile 'HK' "$TARGET_CONF" "$HK_CONF")"
  TW_BACKUP="$(filter_profile 'TW' "$TARGET_CONF" "$TW_CONF")"
  HK_TW_BACKUP="$(filter_profile 'HK_TW' "$TARGET_CONF" "$HK_TW_CONF")"
fi

/bin/mkdir -p "$(/usr/bin/dirname "$OPS_LOG")"
TS="$(/bin/date -u +%Y-%m-%dT%H:%M:%SZ)"
LINK_HOST="$(/bin/echo "$SUB_LINK" | /usr/bin/sed -E 's#^https?://([^/]+).*$#\1#')"
LINK_PATH="$(/bin/echo "$SUB_LINK" | /usr/bin/sed -E 's#^https?://[^/]+(/[^?]*).*$#\1#')"
[[ "$LINK_PATH" == "$SUB_LINK" ]] && LINK_PATH='/'

if [[ "$UPDATE_DERIVED" == 'yes' ]]; then
  /usr/bin/printf '{"timestamp":"%s","target":"surge-profile","operation":"update_from_subscription_link","setting_paths":["%s","%s","%s","%s"],"old_value_summary":"PaoluzX main profile and derived files before update","new_value_summary":"Main profile refreshed from subscription and derived HK/TW/HK+TW files regenerated","backup_path":{"main":"%s","hk":"%s","tw":"%s","hk_tw":"%s"},"rollback_instruction":"restore from backups per file","verification":"downloaded profile contains [Proxy], derived outputs pass region checks","confirmation_required":false,"confirmation_received":false,"subscription_source":{"host":"%s","path":"%s","query_redacted":true}}\n' \
    "$TS" "$TARGET_CONF" "$HK_CONF" "$TW_CONF" "$HK_TW_CONF" "$MAIN_BACKUP" "$HK_BACKUP" "$TW_BACKUP" "$HK_TW_BACKUP" "$LINK_HOST" "$LINK_PATH" >> "$OPS_LOG"
else
  /usr/bin/printf '{"timestamp":"%s","target":"surge-profile","operation":"update_from_subscription_link","setting_paths":["%s"],"old_value_summary":"PaoluzX main profile before update","new_value_summary":"Main profile refreshed from subscription; derived update skipped by parameter","backup_path":{"main":"%s"},"rollback_instruction":"restore main from backup","verification":"downloaded profile contains [Proxy]","confirmation_required":false,"confirmation_received":false,"subscription_source":{"host":"%s","path":"%s","query_redacted":true}}\n' \
    "$TS" "$TARGET_CONF" "$MAIN_BACKUP" "$LINK_HOST" "$LINK_PATH" >> "$OPS_LOG"
fi

echo "Updated main profile: $TARGET_CONF"
echo "Main backup: $MAIN_BACKUP"
echo "Derived update: $UPDATE_DERIVED"
if [[ "$UPDATE_DERIVED" == 'yes' ]]; then
  echo "Updated: $HK_CONF"
  echo "Updated: $TW_CONF"
  echo "Updated: $HK_TW_CONF"
fi
