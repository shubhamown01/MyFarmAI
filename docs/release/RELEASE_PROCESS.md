# MyFarmAI Release Process

**Status:** Adopted (2026-11-09)

## Branching strategy

| Branch | Purpose | Rules |
|---|---|---|
| `main` | Stable production code. Protected-ish; PRs preferred for non-trivial changes. | Tagged releases cut from `main`. |
| `develop` | Integration & testing. | Features merge here first; promoted to `main` after gates pass. |
| `feature/*` | One feature per branch, cut from `develop`. | PR → `develop`. |
| `release/*` | Release preparation (`release/v1.0.0`). | Only fixes/docs allowed; merges to `main` and `develop`. |
| `hotfix/*` | Urgent prod fix, cut from `main`. | PR → `main` AND backport to `develop`; increments PATCH. |

Do not overwrite or discard existing branches. `phase-01-foundation` is kept as
an historical integration branch (fast-forwarded into `main`, all commits
preserved).

## Release flow (target: stable release vMAJOR.MINOR.PATCH)

1. **Cut** `release/vX.Y.Z` from `develop` (or `main` for a hotfix from the
   parent release tag → `hotfix/vX.Y.(Z+1)`).
2. **Bump versions** per `VERSIONING_POLICY.md`; run the manifest-consistency
   check (`.github/workflows/release.yml` job or manual `grep`); commit.
3. **Gates** (§9 of the release mandate): lint, typecheck, backend tests, web
   tests/build, Android release build, live prod verification. All must be
   evidence-backed in `docs/release/VX.Y.Z_RELEASE_CHECKLIST.md`.
4. **Owner approval gate** — explicit human approval before tagging/publication.
5. **Tag** `vX.Y.Z` on the release commit on `main`; push the tag only.
6. **CI release pipeline** (`.github/workflows/release.yml`) builds the signed
   APK/AAB, generates SHA-256 checksums, attaches artifacts to a **draft**
   GitHub Release.
7. **Publish** the release (owner-approved); verify anonymous download.
8. **Post-merge** back to `develop` (release notes/version bumps).

## Playbook with commands

```bash
git checkout develop && git checkout -b release/v1.0.0
# bump versions (VERSION, android/app.json, build.gradle versionCode/Name,
# web/package.json, backend/pyproject.toml), then:
git commit -m "chore(release): v1.0.0"
git checkout main && git merge --no-ff release/v1.0.0
git tag v1.0.0 && git push origin main --tags
```

## Notes

- Production deployment (Catalyst AppSail web/backend) uses the AppSail image
  process in `docs/deployment/DEPLOYMENT_RUNBOOK.md` — a code release and a
  deployment are separate operations; the runbook must be kept in sync with
  the tagged commit.
- `gh` CLI (admin `shubhamown01`) is the release administration path; GitHub
  Actions workflows run least-privilege (see workflows' `permissions:`).
