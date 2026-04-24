#!/bin/zsh
set -euo pipefail

TARGET_CONF='/Users/lancer/Library/Application Support/Surge/Profiles/PaoluzX.conf'
MODE='HK'
OPS_LOG='/Users/lancer/projects/homelab-agent/var/ops-log.jsonl'

if [[ ! -f "$TARGET_CONF" ]]; then
  echo "Source profile not found: $TARGET_CONF" >&2
  exit 1
fi

TMP="$(mktemp "/tmp/PaoluzX.conf.${MODE}.XXXXXX")"
BACKUP="${TARGET_CONF}.bak.$(/bin/date +%Y%m%d-%H%M%S)"
trap 'rm -f "$TMP"' EXIT

/usr/bin/awk -v mode="$MODE" '
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
  return is_hk_name(name)
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
' "$TARGET_CONF" "$TARGET_CONF" > "$TMP"

if ! /usr/bin/grep -q '^\[Proxy\]' "$TMP"; then
  echo "Generated profile has no [Proxy] section; refusing to overwrite $TARGET_CONF" >&2
  exit 1
fi

if ! /usr/bin/awk '
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
{
  line = $0
  sub(/\r$/, "", line)
  if (line ~ /^\[/) {
    section = line
  } else if (section == "[Proxy]" && line !~ /^[ \t]*(#|$)/ && index(line, "=") > 0) {
    name = proxy_name(line)
    if (is_hk_name(name)) {
      found = 1
    } else {
      print "Non-target proxy remains: " name > "/dev/stderr"
      bad = 1
    }
  }
}
END {
  if (!found) {
    exit 2
  }
  exit bad
}
' "$TMP"; then
  echo "Generated profile validation failed for mode $MODE; refusing to overwrite $TARGET_CONF" >&2
  exit 1
fi

KEPT_COUNT="$(/usr/bin/awk '
{
  line = $0
  sub(/\r$/, "", line)
  if (line ~ /^\[/) {
    section = line
  } else if (section == "[Proxy]" && line !~ /^[ \t]*(#|$)/ && index(line, "=") > 0) {
    count++
  }
}
END { print count + 0 }
' "$TMP")"

/bin/cp -p "$TARGET_CONF" "$BACKUP"
/bin/mv "$TMP" "$TARGET_CONF"
trap - EXIT

/bin/mkdir -p "$(/usr/bin/dirname "$OPS_LOG")"
TS="$(/bin/date -u +%Y-%m-%dT%H:%M:%SZ)"
/usr/bin/printf '{"timestamp":"%s","target":"surge-profile","operation":"filter_proxy_region_hk","setting_paths":["%s"],"old_value_summary":"full profile before HK-only filtering","new_value_summary":"HK-only profile, kept_proxies=%s","backup_path":"%s","rollback_instruction":"cp -p %s %s","verification":"section [Proxy] contains only HK-tagged entries","confirmation_required":false,"confirmation_received":false}\n' \
  "$TS" "$TARGET_CONF" "$KEPT_COUNT" "$BACKUP" "$BACKUP" "$TARGET_CONF" >> "$OPS_LOG"

echo "Updated: $TARGET_CONF"
echo "Backup: $BACKUP"
echo "Kept proxies: $KEPT_COUNT"
