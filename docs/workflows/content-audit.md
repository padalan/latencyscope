---
description: Full content audit before publishing or major updates
---

# Content Audit Workflow

Run this audit to ensure all content meets quality standards before publishing.

## 1. Em Dash Check
// turbo
```bash
grep -rn " - \|-" src/content/learn/*.md src/content/blog/*.md | wc -l
```
**Pass criteria:** Output should be `0`. If not, run:
```bash
find src/content -name "*.md" -exec sed -i '' 's/ - /-/g; s/-/-/g' {} \;
```

## 2. Weak Language Check
// turbo
```bash
grep -rni "simply\|just a\|basically\|it's essentially\|really just" src/content/learn/*.md src/content/blog/*.md | head -20
```
**Pass criteria:** Review each match. Replace weak phrasing with authoritative language.

## 3. Banned Words Check
// turbo
```bash
grep -rni "delve\|synerg\|paradigm\|holistic\|utilize" src/content/learn/*.md src/content/blog/*.md | head -20
```
**Pass criteria:** Output should be `0` or only false positives.

## 4. Internal Linking Opportunities
// turbo
```bash
# Check for unlinked MEV mentions
grep -rn "MEV\|block builder" src/content/learn/*.md | grep -v "\[" | head -10

# Check for unlinked HugePages/THP mentions
grep -rn "HugePages\|THP\|Transparent Huge" src/content/learn/*.md | grep -v "\[" | head -10
```
**Pass criteria:** Key topics should link to their dedicated lessons.

## 5. CTA Coverage Check
// turbo
```bash
echo "=== Posts missing CTAs ==="
grep -rL "opportunities\|latency-audit" src/content/blog/*.md
```
**Pass criteria:** Every blog post should have a CTA to `/opportunities` or `/tools/latency-audit`.

## 6. TypeScript Check
// turbo
```bash
npx astro check 2>&1 | grep -E "error|warning" | head -20
```
**Pass criteria:** No errors in src/utils/ (test file warnings are acceptable).

## 7. Build Verification
```bash
pnpm run build
```
**Pass criteria:** Build must complete without errors.

---

## Quick Full Audit (One Command)
// turbo
```bash
echo "=== Em Dashes ===" && grep -rn " - \|-" src/content/learn/*.md src/content/blog/*.md | wc -l && \
echo "=== Weak Language ===" && grep -rni "simply\|just a\|basically" src/content/learn/*.md src/content/blog/*.md | wc -l && \
echo "=== Missing CTAs ===" && grep -rL "opportunities\|latency-audit" src/content/blog/*.md | wc -l
```
