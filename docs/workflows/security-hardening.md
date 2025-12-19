---
description: How to secure the repository (Branch Protection, PyPI OIDC, Scanning)
---

# Security Hardening Guide

This workflow details how to secure the `latencyscope` repository on GitHub and PyPI.

## 1. GitHub Branch Protection Rules
**Goal:** Prevent direct pushes to `main` and ensure code quality.

1. Go to **Settings** > **Branches**.
2. Click **Add branch protection rule**.
3. **Branch name pattern**: `main`
4. Check the following options:
   - [x] **Require a pull request before merging**
     - [x] **Require approvals**: `1`
     - [x] **Dismiss stale pull request approvals when new commits are pushed**
   - [x] **Require status checks to pass before merging**
     - Search for and select: `test (3.11)` (or your matrix job names), `mypy`.
   - [x] **Require conversation resolution before merging**
   - [x] **Require linear history** (optional, keeps git history clean)
   - [x] **Include administrators** (enforce rules on everyone)

## 2. PyPI Trusted Publishing (OIDC)
**Goal:** Eliminate long-lived API tokens for releases.

*Note: Your `publish.yml` is already configured for this.*

1. Go to [PyPI.org](https://pypi.org/manage/project/latencyscope/settings/publishing/).
2. Scroll to **Trusted Publishing**.
3. Click **Add a new publisher**.
4. **Owner**: `padalan`
5. **Repository name**: `latencyscope`
6. **Workflow name**: `publish.yml`
7. **Environment name**: `release`

## 3. Automated Security Scanning
**Goal:** Detect vulnerabilities automatically.

### OSSF Scorecard
*Status: Added in `.github/workflows/scorecard.yml`*
- Runs weekly and on push to `main`.
- checks for bad practices (binary blobs, unpinned dependencies, etc.).
- Results appear in the **Security** tab > **Code Scanning**.

### Dependabot
1. Create `.github/dependabot.yml` (if not exists):
   ```yaml
   version: 2
   updates:
     - package-ecosystem: "pip"
       directory: "/"
       schedule:
         interval: "weekly"
     - package-ecosystem: "github-actions"
       directory: "/"
       schedule:
         interval: "weekly"
   ```

## 4. Repository Settings
1. **Settings** > **Code security and analysis**:
   - [x] **Dependabot alerts**: Enable
   - [x] **Dependabot security updates**: Enable
   - [x] **Secret scanning**: Enable (if public)
   - [x] **Push protection**: Enable

## 5. Security Policy
*Status: Exists (`SECURITY.md`)*
- Ensure `security@nikhilpadala.com` is monitored.
