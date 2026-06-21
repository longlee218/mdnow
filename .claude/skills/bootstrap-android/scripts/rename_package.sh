#!/usr/bin/env bash
set -euo pipefail

# ─── Colors & Symbols ────────────────────────────────────────────────────────
if [[ -t 1 ]]; then
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[1;33m'
  CYAN='\033[0;36m'
  BOLD='\033[1m'
  DIM='\033[2m'
  RESET='\033[0m'
else
  RED='' GREEN='' YELLOW='' CYAN='' BOLD='' DIM='' RESET=''
fi

log_info()    { printf "${GREEN}✔${RESET} %s\n" "$*"; }
log_warn()    { printf "${YELLOW}⚠${RESET} %s\n" "$*"; }
log_error()   { printf "${RED}✖${RESET} %s\n" "$*" >&2; }
log_step()    { printf "${CYAN}▸${RESET} %s\n" "$*"; }
log_verbose() { [[ "$VERBOSE" -eq 1 ]] && printf "  ${DIM}%s${RESET}\n" "$*" || true; }

# ─── Usage ────────────────────────────────────────────────────────────────────
usage() {
  cat <<'EOF'
Rename Android package name quickly and safely.

Usage:
  rename_package.sh --new <new.package.name> [OPTIONS]

Required:
  --new             New package name, e.g. com.company.myapp

Options:
  --old             Old package name. Auto-detected from build.gradle(.kts) if omitted
  --apply           Execute changes (default: dry-run)
  --project-root    Project root path (default: current directory)
  --modules         Comma-separated list of modules to process (default: auto-detect all)
  --no-backup       Skip creating backup before applying
  --run-build       Run ./gradlew assembleDebug after rename
  --verbose         Show detailed output for each replacement
  -h, --help        Show this help

Examples:
  rename_package.sh --new com.acme.aiproject
  rename_package.sh --old com.example.app --new com.acme.aiproject --apply
  rename_package.sh --new com.acme.aiproject --apply --modules app,feature:core
  rename_package.sh --new com.acme.aiproject --apply --run-build --verbose
EOF
}

# ─── Defaults ─────────────────────────────────────────────────────────────────
PROJECT_ROOT="$(pwd)"
OLD_PACKAGE=""
NEW_PACKAGE=""
APPLY=0
RUN_BUILD=0
VERBOSE=0
NO_BACKUP=0
USER_MODULES=""
HAS_RG=0

command -v rg >/dev/null 2>&1 && HAS_RG=1

# ─── Parse arguments ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --old)          OLD_PACKAGE="${2:-}";   shift 2 ;;
    --new)          NEW_PACKAGE="${2:-}";   shift 2 ;;
    --apply)        APPLY=1;               shift   ;;
    --project-root) PROJECT_ROOT="${2:-}";  shift 2 ;;
    --modules)      USER_MODULES="${2:-}";  shift 2 ;;
    --no-backup)    NO_BACKUP=1;           shift   ;;
    --run-build)    RUN_BUILD=1;           shift   ;;
    --verbose)      VERBOSE=1;             shift   ;;
    -h|--help)      usage; exit 0                  ;;
    *)              log_error "Unknown option: $1"; usage; exit 1 ;;
  esac
done

# ─── Validate inputs ─────────────────────────────────────────────────────────
if [[ -z "$NEW_PACKAGE" ]]; then
  log_error "Missing required flag: --new <new.package.name>"
  exit 1
fi

is_valid_package() {
  [[ "$1" =~ ^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$ ]]
}

if ! is_valid_package "$NEW_PACKAGE"; then
  log_error "Invalid --new package: '$NEW_PACKAGE'"
  echo "  Expected format: lower.case.package (e.g. com.company.app)" >&2
  exit 1
fi

# ─── Locate build files (Groovy + Kotlin DSL) ────────────────────────────────
find_build_file() {
  local dir="$1"
  if [[ -f "$dir/build.gradle.kts" ]]; then
    echo "$dir/build.gradle.kts"
  elif [[ -f "$dir/build.gradle" ]]; then
    echo "$dir/build.gradle"
  fi
}

find_settings_file() {
  if [[ -f "$PROJECT_ROOT/settings.gradle.kts" ]]; then
    echo "$PROJECT_ROOT/settings.gradle.kts"
  elif [[ -f "$PROJECT_ROOT/settings.gradle" ]]; then
    echo "$PROJECT_ROOT/settings.gradle"
  fi
}

# ─── Detect modules ──────────────────────────────────────────────────────────
detect_modules() {
  local settings_file
  settings_file="$(find_settings_file)"
  if [[ -z "$settings_file" ]]; then
    # Fallback: just check if app/ exists
    if [[ -d "$PROJECT_ROOT/app" ]]; then
      echo "app"
    fi
    return
  fi

  # Extract include/include(":module") patterns from settings file
  perl -ne '
    while (/include\s*\(?\s*"?:?([^")\s,]+)"?\s*\)?/g) {
      my $mod = $1;
      $mod =~ s/:/\//g;
      print "$mod\n";
    }
  ' "$settings_file" | sort -u
}

MODULES=()
if [[ -n "$USER_MODULES" ]]; then
  IFS=',' read -ra MODULES <<< "$USER_MODULES"
else
  while IFS= read -r mod; do
    [[ -n "$mod" ]] && MODULES+=("$mod")
  done < <(detect_modules)
fi

if [[ "${#MODULES[@]}" -eq 0 ]]; then
  log_error "No modules detected. Pass --modules or ensure settings.gradle(.kts) exists."
  exit 1
fi

# ─── Detect old package ──────────────────────────────────────────────────────
detect_old_package() {
  local build_file="$1"
  local value
  # Try namespace first, then applicationId
  value="$(perl -ne 'if (/namespace\s*[=(]\s*"([^"]+)"/) { print $1; exit }' "$build_file")"
  if [[ -n "$value" ]]; then echo "$value"; return; fi
  value="$(perl -ne 'if (/applicationId\s*[=(]\s*"([^"]+)"/) { print $1; exit }' "$build_file")"
  echo "$value"
}

if [[ -z "$OLD_PACKAGE" ]]; then
  # Try each module until we find a package
  for mod in "${MODULES[@]}"; do
    mod_dir="$PROJECT_ROOT/$mod"
    build_file="$(find_build_file "$mod_dir")"
    if [[ -n "$build_file" ]]; then
      OLD_PACKAGE="$(detect_old_package "$build_file")"
      [[ -n "$OLD_PACKAGE" ]] && break
    fi
  done
fi

OLD_PACKAGE="$(echo "$OLD_PACKAGE" | tr -d '[:space:]')"
NEW_PACKAGE="$(echo "$NEW_PACKAGE" | tr -d '[:space:]')"

if [[ -z "$OLD_PACKAGE" ]]; then
  log_error "Cannot auto-detect old package. Please pass --old <old.package.name>."
  exit 1
fi

if [[ "$OLD_PACKAGE" == "$NEW_PACKAGE" ]]; then
  log_error "Old and new package are the same: $OLD_PACKAGE"
  exit 1
fi

if ! [[ "$OLD_PACKAGE" =~ ^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z][A-Za-z0-9_]*)+$ ]]; then
  log_error "Detected old package looks invalid: '$OLD_PACKAGE'"
  echo "  Please provide it explicitly with --old." >&2
  exit 1
fi

OLD_PATH="$(echo "$OLD_PACKAGE" | tr '.' '/')"
NEW_PATH="$(echo "$NEW_PACKAGE" | tr '.' '/')"

# ─── Header ──────────────────────────────────────────────────────────────────
echo ""
printf "${BOLD}╔══════════════════════════════════════════╗${RESET}\n"
printf "${BOLD}║   Android Package Rename Tool v2.0       ║${RESET}\n"
printf "${BOLD}╚══════════════════════════════════════════╝${RESET}\n"
echo ""
printf "  ${DIM}Project root${RESET}  : ${BOLD}%s${RESET}\n" "$PROJECT_ROOT"
printf "  ${DIM}Old package${RESET}   : ${RED}%s${RESET}\n" "$OLD_PACKAGE"
printf "  ${DIM}New package${RESET}   : ${GREEN}%s${RESET}\n" "$NEW_PACKAGE"
printf "  ${DIM}Modules${RESET}       : ${CYAN}%s${RESET}\n" "${MODULES[*]}"
if [[ "$APPLY" -eq 1 ]]; then
  printf "  ${DIM}Mode${RESET}          : ${RED}${BOLD}APPLY${RESET}\n"
else
  printf "  ${DIM}Mode${RESET}          : ${GREEN}DRY-RUN${RESET}\n"
fi
echo ""

# ─── Search helpers ───────────────────────────────────────────────────────────
EXCLUDE_DIRS=(build .gradle .idea generated .git node_modules)

search_files_containing() {
  local needle="$1"
  local target="$2"

  if [[ "$HAS_RG" -eq 1 ]]; then
    local globs=()
    for d in "${EXCLUDE_DIRS[@]}"; do globs+=(--glob "!**/$d/**"); done
    rg -l --fixed-strings "${globs[@]}" "$needle" "$target" 2>/dev/null || true
    return
  fi

  local excludes=()
  for d in "${EXCLUDE_DIRS[@]}"; do excludes+=(--exclude-dir="$d"); done

  if [[ -d "$target" ]]; then
    grep -RIlF "${excludes[@]}" -- "$needle" "$target" 2>/dev/null || true
  elif [[ -f "$target" ]]; then
    grep -lF -- "$needle" "$target" 2>/dev/null || true
  fi
}

search_hits_with_lines() {
  local needle="$1"
  local target="$2"

  if [[ "$HAS_RG" -eq 1 ]]; then
    local globs=()
    for d in "${EXCLUDE_DIRS[@]}"; do globs+=(--glob "!**/$d/**"); done
    rg -n --fixed-strings "${globs[@]}" "$needle" "$target" 2>/dev/null || true
    return
  fi

  local excludes=()
  for d in "${EXCLUDE_DIRS[@]}"; do excludes+=(--exclude-dir="$d"); done

  if [[ -d "$target" ]]; then
    grep -RInF "${excludes[@]}" -- "$needle" "$target" 2>/dev/null || true
  elif [[ -f "$target" ]]; then
    grep -nF -- "$needle" "$target" 2>/dev/null || true
  fi
}

# ─── Collect targets ─────────────────────────────────────────────────────────
TARGETS=()

# Module directories & build files
for mod in "${MODULES[@]}"; do
  mod_dir="$PROJECT_ROOT/$mod"
  [[ -d "$mod_dir" ]] && TARGETS+=("$mod_dir")
done

# Root build files
root_build="$(find_build_file "$PROJECT_ROOT")"
[[ -n "$root_build" ]] && TARGETS+=("$root_build")

settings_file="$(find_settings_file)"
[[ -n "$settings_file" ]] && TARGETS+=("$settings_file")

# buildSrc
[[ -d "$PROJECT_ROOT/buildSrc" ]] && TARGETS+=("$PROJECT_ROOT/buildSrc")

# google-services.json files across all modules
for mod in "${MODULES[@]}"; do
  gs_file="$PROJECT_ROOT/$mod/google-services.json"
  [[ -f "$gs_file" ]] && TARGETS+=("$gs_file")
done

# ─── Find files to replace ───────────────────────────────────────────────────
REPLACE_FILES=()
for target in "${TARGETS[@]}"; do
  if [[ -e "$target" ]]; then
    while IFS= read -r file; do
      [[ -n "$file" ]] && REPLACE_FILES+=("$file")
    done < <(search_files_containing "$OLD_PACKAGE" "$target")
  fi
done

# Deduplicate
if [[ "${#REPLACE_FILES[@]}" -gt 0 ]]; then
  UNIQUE=()
  while IFS= read -r line; do
    UNIQUE+=("$line")
  done < <(printf '%s\n' "${REPLACE_FILES[@]}" | awk '!seen[$0]++')
  REPLACE_FILES=("${UNIQUE[@]}")
fi

# ─── Find source directories to move ─────────────────────────────────────────
SOURCE_SETS=(main test androidTest)
LANG_DIRS=(java kotlin)

MOVE_OLD_DIRS=()
MOVE_NEW_DIRS=()
for mod in "${MODULES[@]}"; do
  for ss in "${SOURCE_SETS[@]}"; do
    for lang in "${LANG_DIRS[@]}"; do
      old_dir="$PROJECT_ROOT/$mod/src/$ss/$lang/$OLD_PATH"
      new_dir="$PROJECT_ROOT/$mod/src/$ss/$lang/$NEW_PATH"
      if [[ -d "$old_dir" ]]; then
        MOVE_OLD_DIRS+=("$old_dir")
        MOVE_NEW_DIRS+=("$new_dir")
      fi
    done
  done
done

# ─── Summary ─────────────────────────────────────────────────────────────────
printf "${BOLD}── Files to replace (%d) ──${RESET}\n" "${#REPLACE_FILES[@]}"
if [[ "${#REPLACE_FILES[@]}" -gt 0 ]]; then
  for f in "${REPLACE_FILES[@]}"; do
    local_path="${f#"$PROJECT_ROOT/"}"
    echo "  ${DIM}•${RESET} $local_path"
  done
fi

echo ""
printf "${BOLD}── Directories to move (%d) ──${RESET}\n" "${#MOVE_OLD_DIRS[@]}"
for i in "${!MOVE_OLD_DIRS[@]}"; do
  old_rel="${MOVE_OLD_DIRS[$i]#"$PROJECT_ROOT/"}"
  new_rel="${MOVE_NEW_DIRS[$i]#"$PROJECT_ROOT/"}"
  echo "  ${DIM}•${RESET} $old_rel ${YELLOW}→${RESET} $new_rel"
done

if [[ "${#REPLACE_FILES[@]}" -eq 0 && "${#MOVE_OLD_DIRS[@]}" -eq 0 ]]; then
  log_warn "Nothing to do — no files contain '$OLD_PACKAGE' and no directories to move."
  exit 0
fi

# ─── Dry-run exit ─────────────────────────────────────────────────────────────
if [[ "$APPLY" -eq 0 ]]; then
  echo ""
  printf "${YELLOW}Dry-run complete.${RESET} Run with ${BOLD}--apply${RESET} to execute:\n"
  echo "  $0 --old $OLD_PACKAGE --new $NEW_PACKAGE --apply"
  exit 0
fi

# ─── Write permission check ──────────────────────────────────────────────────
for f in "${REPLACE_FILES[@]}"; do
  if [[ ! -w "$f" ]]; then
    log_error "No write permission: $f"
    exit 1
  fi
done

# ─── Backup ──────────────────────────────────────────────────────────────────
if [[ "$NO_BACKUP" -eq 0 ]]; then
  TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
  BACKUP_FILE="$PROJECT_ROOT/.rename_backup_${TIMESTAMP}.tar.gz"

  echo ""
  log_step "Creating backup..."

  # Collect all files and dirs that will be modified
  BACKUP_PATHS=()
  for f in "${REPLACE_FILES[@]}"; do
    BACKUP_PATHS+=("${f#"$PROJECT_ROOT/"}")
  done
  for d in "${MOVE_OLD_DIRS[@]}"; do
    BACKUP_PATHS+=("${d#"$PROJECT_ROOT/"}")
  done

  tar -czf "$BACKUP_FILE" -C "$PROJECT_ROOT" "${BACKUP_PATHS[@]}" 2>/dev/null || true
  log_info "Backup saved: $(basename "$BACKUP_FILE")"
  log_verbose "Restore with: tar -xzf $BACKUP_FILE -C $PROJECT_ROOT"
fi

# ─── Apply: Replace text ─────────────────────────────────────────────────────
echo ""
log_step "Replacing package name in files..."

replace_text_in_file() {
  local file="$1"
  OLD_PACKAGE="$OLD_PACKAGE" NEW_PACKAGE="$NEW_PACKAGE" \
    perl -0777 -i -pe 's/\Q$ENV{OLD_PACKAGE}\E/$ENV{NEW_PACKAGE}/g' "$file"
}

TOTAL="${#REPLACE_FILES[@]}"
COUNT=0
for f in "${REPLACE_FILES[@]}"; do
  COUNT=$((COUNT + 1))
  local_path="${f#"$PROJECT_ROOT/"}"
  printf "  ${DIM}[%d/%d]${RESET} %s\n" "$COUNT" "$TOTAL" "$local_path"
  replace_text_in_file "$f"
done
log_info "Replaced in $TOTAL file(s)"

# ─── Apply: Move directories ─────────────────────────────────────────────────
move_tree_contents() {
  local from="$1"
  local to="$2"

  mkdir -p "$to"

  while IFS= read -r -d '' src_file; do
    local rel="${src_file#"$from"/}"
    local dest="$to/$rel"
    mkdir -p "$(dirname "$dest")"
    if [[ -e "$dest" ]]; then
      log_error "Collision detected. Destination already exists: $dest"
      exit 1
    fi
    mv "$src_file" "$dest"
    log_verbose "Moved: ${src_file#"$PROJECT_ROOT/"} → ${dest#"$PROJECT_ROOT/"}"
  done < <(find "$from" -type f -print0)

  # Remove empty old directories, follow symlinks safely
  find "$from" -type d -empty -delete 2>/dev/null || true
}

if [[ "${#MOVE_OLD_DIRS[@]}" -gt 0 ]]; then
  echo ""
  log_step "Moving source directories..."
  for i in "${!MOVE_OLD_DIRS[@]}"; do
    old_rel="${MOVE_OLD_DIRS[$i]#"$PROJECT_ROOT/"}"
    new_rel="${MOVE_NEW_DIRS[$i]#"$PROJECT_ROOT/"}"
    printf "  ${DIM}[%d/%d]${RESET} %s ${YELLOW}→${RESET} %s\n" "$((i+1))" "${#MOVE_OLD_DIRS[@]}" "$old_rel" "$new_rel"
    move_tree_contents "${MOVE_OLD_DIRS[$i]}" "${MOVE_NEW_DIRS[$i]}"
  done
  log_info "Moved ${#MOVE_OLD_DIRS[@]} directory tree(s)"
fi

# ─── Post-checks ─────────────────────────────────────────────────────────────
echo ""
log_step "Running post-checks..."

POST_CHECK_TARGETS=()
for mod in "${MODULES[@]}"; do
  mod_dir="$PROJECT_ROOT/$mod"
  [[ -d "$mod_dir/src" ]]                       && POST_CHECK_TARGETS+=("$mod_dir/src")
  build_f="$(find_build_file "$mod_dir")"
  [[ -n "$build_f" ]]                            && POST_CHECK_TARGETS+=("$build_f")
  [[ -f "$mod_dir/src/main/AndroidManifest.xml" ]] && POST_CHECK_TARGETS+=("$mod_dir/src/main/AndroidManifest.xml")
  [[ -f "$mod_dir/google-services.json" ]]       && POST_CHECK_TARGETS+=("$mod_dir/google-services.json")
done

REMAINING_HITS=0
for target in "${POST_CHECK_TARGETS[@]}"; do
  if [[ -e "$target" ]]; then
    hits="$(search_hits_with_lines "$OLD_PACKAGE" "$target")"
    if [[ -n "$hits" ]]; then
      REMAINING_HITS=1
      target_rel="${target#"$PROJECT_ROOT/"}"
      log_warn "Old package still found in: $target_rel"
      echo "$hits" | head -20
      echo ""
    fi
  fi
done

# ─── Final summary ───────────────────────────────────────────────────────────
echo ""
printf "${BOLD}╔══════════════════════════════════════════╗${RESET}\n"
if [[ "$REMAINING_HITS" -eq 1 ]]; then
  printf "${BOLD}║${RESET}  ${YELLOW}⚠ Rename completed with warnings${RESET}        ${BOLD}║${RESET}\n"
else
  printf "${BOLD}║${RESET}  ${GREEN}✔ Rename completed successfully${RESET}          ${BOLD}║${RESET}\n"
fi
printf "${BOLD}╚══════════════════════════════════════════╝${RESET}\n"
echo ""
printf "  Files replaced     : ${BOLD}%d${RESET}\n" "${#REPLACE_FILES[@]}"
printf "  Dirs moved         : ${BOLD}%d${RESET}\n" "${#MOVE_OLD_DIRS[@]}"
printf "  Modules processed  : ${BOLD}%s${RESET}\n" "${MODULES[*]}"
if [[ "$NO_BACKUP" -eq 0 && -n "${BACKUP_FILE:-}" ]]; then
  printf "  Backup             : ${DIM}%s${RESET}\n" "$(basename "$BACKUP_FILE")"
fi
echo ""

if [[ "$REMAINING_HITS" -eq 1 ]]; then
  log_warn "Some references to the old package remain. Please review manually."
  exit 2
fi

# ─── Optional build ──────────────────────────────────────────────────────────
if [[ "$RUN_BUILD" -eq 1 ]]; then
  echo ""
  log_step "Running build check: ./gradlew assembleDebug"
  (cd "$PROJECT_ROOT" && ./gradlew assembleDebug)
fi
