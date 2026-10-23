---
name: myfarmai-compose-review
description: Review MyFarmAI Docker Compose changes against project architecture, data safety, security, and resource constraints.
compatibility: opencode
---

# MyFarmAI Compose Review

## When to use
Use this skill before reviewing or proposing changes to the
MyFarmAI Docker Compose configuration.

## Required workflow
1. Read the repository AGENTS.md instructions.
2. Read the docker-compose-patterns skill.
3. Read docker-destructive-guardrails when cleanup or deletion is relevant.
4. Inspect the existing configuration before proposing changes.
5. Preserve existing services and persistent data unless a change is approved.
6. Check service dependencies, health checks, networks, volumes,
   secrets handling, and resource limits.
7. Consider the development machine's limited RAM, swap, and SSD capacity.
8. Prefer minimal changes over new infrastructure.
9. Do not introduce Kubernetes without an explicit project requirement.
10. Report findings, proposed changes, risks, and verification steps
    before editing files.

## Safety
Never run destructive Docker commands without following the relevant
skill's confirmation requirements.
Never print secrets from environment files or resolved configuration.
Never claim validation succeeded unless it was actually performed.
