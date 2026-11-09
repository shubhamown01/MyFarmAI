# MyFarmAI Android Signing & Key Recovery

**Status:** Adopted (v1.0.0 preparation, 2026-11-09)

## Identity

- **Application ID:** `com.myfarmai.android` — stable across v1.x; DO NOT change casually (existing installs cannot upgrade to a different application ID).
- **Signing key:** a single production keypair signs every published APK/AAB. Future updates must preserve this identity or Android will refuse the upgrade (`INSTALL_FAILED_UPDATE_INCOMPATIBLE`).

## Key facts

- Keystore created once for v1.0.0: **outside the repository**, path on the
  owner machine: `/data/MyFarmAI-keys/myfarmai-release.jks`
  (never `git add`ed; `.gitignore` blocks `*.jks`/`*.keystore` project-relative
  copies — verify with `git check-ignore`).
- Key file **and** passwords live only outside Git. Passwords are stored in the
  local shell-protected file `/data/MyFarmAI-keys/keystore.env`
  (`MYFARMAI.Android.Key=…` credentials, mode 600).
- `gradle.properties` must never contain keystore credentials; the release
  build reads env vars or a local, uncommitted `android/android/app/release.gradle`.

## Local build-time wiring (reproducible)

```bash
set -a; . /data/MyFarmAI-keys/keystore.env; set +a
cd /data/MyFarmAI/android/android
./gradlew :app:assembleRelease
```

Gradle reads `MYFARMAI_KEYSTORE_PATH`, `MYFARMAI_KEYSTORE_PASSWORD`,
`MYFARMAI_KEY_ALIAS`, `MYFARMAI_KEY_PASSWORD` from the environment
(defined in `app/build.gradle` via `System.getenv(...)`, not literals).

## Verification

```bash
# Who signed it (must map to the release key, NOT debug):
$ANDROID_BUILD_TOOLS/apksigner verify --print-certs \
  /data/MyFarmAI/android/android/app/build/outputs/apk/release/app-release.apk
```

Expected: one signing cert; its `Subject DN CN=MyFarmAI Release`; SHA-256 of
the cert recorded below at key creation.

## Ownership and recovery

- Key owner: project owner (Mr. Shubham — GitHub `shubhamown01`). Only the
  owner (or an agent with the owner's explicit instruction) may use
  `/data/MyFarmAI-keys/`.
- Backup: one (1) copy of the `.jks` and `keystore.env` on an offline medium
  (USB drive held by owner), stored after key creation; documented by the
  owner in a private note, NOT in this repository.
- **If the key is lost, apps in user hands forever lose the upgrade path.**
  Replacement requires a new application ID and a reinstall. Protect the
  backup accordingly.
- Rotation (key reset) on Google Play: only supported via Google Play App
  Signing with owner approval; independently redistributable APKs do not
  support rotation — another reason the backup procedure is mandatory.

## What NOT to do

- Never commit `*.jks`, `*.keystore`, `keystore.env`, or paste any key
  material into docs, CI logs, or prompts. CI never signs (signature is made
  on the owner machine) unless short-lived secrets are later added explicitly
  by the owner.
