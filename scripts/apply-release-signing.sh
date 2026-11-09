#!/usr/bin/env bash
# Re-apply release signing config to the generated native Android project
# (expo prebuild output). Idempotent: safe to run repeatedly.
# Run after every `npx expo prebuild`. Credentials come from the environment
# (see /data/MyFarmAI-keys/keystore.env) — never committed.
set -euo pipefail

GRADLE_FILE="android/android/app/build.gradle"
if [ ! -f "$GRADLE_FILE" ]; then
  echo "ERROR: $GRADLE_FILE not found (run 'npx expo prebuild' first)" >&2
  exit 1
fi

if grep -q "MYFARMAI_KEYSTORE_PATH" "$GRADLE_FILE"; then
  echo "release signing config already applied — nothing to do"
  exit 0
fi

python3 - "$GRADLE_FILE" <<'EOF'
import sys, re
path = sys.argv[1]
src = open(path).read()

release_config = '''    signingConfigs {
        release {
            // Release signing reads credentials from the environment only
            // (never committed); docs/release/ANDROID_SIGNING_AND_KEY_RECOVERY.md
            def ksPath = System.getenv("MYFARMAI_KEYSTORE_PATH")
            def ksPass = System.getenv("MYFARMAI_KEYSTORE_PASSWORD")
            def aliasName = System.getenv("MYFARMAI_KEY_ALIAS")
            def keyPassV = System.getenv("MYFARMAI_KEY_PASSWORD")
            if (ksPath && ksPass) {
                storeFile file(ksPath)
                storePassword ksPass
                keyAlias aliasName
                keyPassword keyPassV
            } else {
                storeFile file('debug.keystore')
                storePassword 'android'
                keyAlias 'androiddebugkey'
                keyPassword 'android'
            }
        }
'''

# Insert release config before the closing brace of existing signingConfigs
if "signingConfigs {" not in src:
    print("ERROR: signingConfigs block not found", file=sys.stderr); sys.exit(1)

# add release block inside signingConfigs: find "signingConfigs {\n" then the
# matching first "        }\n    }" debug block end — simplest: insert before
# the first closing of signingConfigs by locating its debug sub-block end.
marker = re.search(r"signingConfigs \{\n(.|\n)*?\n    \}", src)
# Safer: insert right after the opening "signingConfigs {"
src = src.replace("signingConfigs {", "signingConfigs {\n" + release_config, 1)

# Point release buildType at the release config
src = re.sub(
    r"(\n        release \{\n(?:.|\n)*?)signingConfig .*debug.*",
    r"\1signingConfig signingConfigs.release",
    src, count=1)
open(path, "w").write(src)
print("patched:", path)
EOF
echo "NOTE: verify with: ./gradlew :app:assembleRelease + apksigner verify --print-certs"
