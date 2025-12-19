---
description: Full site audit covering code, content, SEO, performance, and security
---

# Full Site Audit Workflow

**Standard:** "Every element must earn its place. Every interaction must build trust."

Execute this audit before major releases or quarterly maintenance.

---

# PHASE 1: CONTENT INTEGRITY (Trust Foundation)

## 1.1 Em Dash Check - Markdown (P0)
// turbo
```bash
echo "=== Em Dash in Markdown ===" && grep -rn " - \|-" src/content/learn/*.md src/content/blog/*.md 2>/dev/null | wc -l
```
**Pass:** 0. Fix with: `find src/content -name "*.md" -exec sed -i '' 's/ - /-/g; s/-/-/g' {} \;`

## 1.1b Em Dash Check - Astro/TSX (P0)
// turbo
```bash
echo "=== Em Dash in Astro/TSX ===" && grep -rn " - \|-" src/pages/*.astro src/pages/**/*.astro src/components/*.tsx src/components/**/*.tsx 2>/dev/null | wc -l
```
**Pass:** 0. Em dashes in UI text are also banned.

## 1.1c Hyphen-Typos Check (P1)
// turbo
```bash
echo "=== Hyphen-Typos (word-is, -is, -the) ===" && grep -rE "[a-z]-is |[a-z]-the |[a-z]-a " src/content/ 2>/dev/null | head -10
```
**Pass:** 0. Pattern like "transactions-is" should be "transactions is" or "transactions, is".

## 1.2 Banned Words Check (P0)
// turbo
```bash
echo "=== Banned Words ===" && grep -rni "game-changing\|seamless\|unparalleled\|cutting-edge\|revolutionary" src/content/ 2>/dev/null | wc -l
```
**Pass:** 0. These destroy B2B credibility.

## 1.3 Weak Language Check (P1)
// turbo
```bash
echo "=== Weak Language ===" && grep -rni "simply\|just a\|just the\|obviously\|basically\|easy to" src/content/ 2>/dev/null | wc -l
```
**Pass:** 0. Replace with authoritative phrasing.

## 1.4 Template Content Hunt (P0)
// turbo
```bash
echo "=== Generic Commands ===" && grep -rE "uname -a|echo 'hello|echo \"hello|sudo apt update" src/content/ 2>/dev/null | wc -l
echo "=== Placeholder Text ===" && grep -rE "TODO:|\\[Insert|lorem ipsum|PLACEHOLDER|Replace this" src/ 2>/dev/null | wc -l
```
**Pass:** 0. All code examples must be topic-specific.

## 1.5 Generic Misconceptions Check (P0)
// turbo
```bash
echo "=== Template Misconceptions ===" && grep -rE "This is too advanced for me|I'll never need|I can just Google" src/content/ 2>/dev/null | wc -l
```
**Pass:** 0. Misconceptions must be topic-specific, not generic.

## 1.6 Vague Claims Check (P1)
// turbo
```bash
echo "=== Vague Claims ===" && grep -rE "many clients|several companies|significant savings|dramatically improved|substantial" src/content/ 2>/dev/null | wc -l
```
**Pass:** 0. Replace with specific numbers (e.g., "$2.1M saved", "18 clients").

---

# PHASE 2: TRUST & AUTHORITY SIGNALS

## 2.1 Specific Metrics Present (GOOD signals)
// turbo
```bash
echo "=== Specific Metrics (Good) ===" && grep -rE "\\$[0-9]+|[0-9]+µs|[0-9]+ms|[0-9]+%" src/content/blog/*.md 2>/dev/null | wc -l
```
**Pass:** High count means good trust signals.

## 2.2 Verification Commands (GOOD signals)
// turbo
```bash
echo "=== Verification Patterns (Good) ===" && grep -rE "verify|check yourself|don't trust me|run this" src/content/ 2>/dev/null | wc -l
```
**Pass:** Should appear in most blog posts.

## 2.3 Accountability Signals (GOOD signals)
// turbo
```bash
echo "=== Accountability (Good) ===" && grep -rni "reach out\|questions\?\|contact me\|let's debug" src/content/ src/components/ 2>/dev/null | wc -l
```
**Pass:** Should appear in blog posts and lesson pages.

## 2.4 Authority Citations (GOOD signals)
// turbo
```bash
echo "=== Kernel/RFC Citations (Good) ===" && grep -rE "kernel/|source code|RFC [0-9]|man [a-z]" src/content/ 2>/dev/null | wc -l
```
**Pass:** Blog posts should cite sources.

---

# PHASE 3: CONTENT STRUCTURE

## 3.1 CTA Coverage (P1)
// turbo
```bash
echo "=== Blog Posts Missing CTAs ===" && grep -rL "opportunities\|latency-audit\|tools/" src/content/blog/*.md 2>/dev/null | wc -l
```
**Pass:** 0. Every blog post needs a CTA.

## 3.2 Internal Link Density (P2)
// turbo
```bash
echo "=== Low Internal Links ===" && for f in src/content/blog/*.md; do count=$(grep -oE "\\](/[a-z]" "$f" 2>/dev/null | wc -l); if [ "$count" -lt 3 ]; then echo "$f: $count links"; fi; done
```
**Pass:** Every post should have 3+ internal links.

## 3.3 Open Loop (Rabbit Hole) Check (P2)
// turbo
```bash
echo "=== Open Loop Patterns ===" && grep -rE "Next:|Continue reading|What's next|we cover in" src/content/blog/*.md 2>/dev/null | wc -l
```
**Pass:** Most posts should end with hooks to other content.

## 3.4 Learn Content Links to Blog (P2)
// turbo
```bash
echo "=== Learn Missing Blog Links ===" && grep -rL "/blog/" src/content/learn/*.md 2>/dev/null | wc -l
```
**Pass:** Each lesson should link to "Pro" version on /blog.

---

# PHASE 4: CODE QUALITY

## 4.1 TypeScript Errors (P0)
// turbo
```bash
echo "=== TypeScript Errors ===" && npx astro check 2>&1 | grep -c "error" || echo "0"
```
**Pass:** 0 errors.

## 4.1b Strict TypeScript Config (P0)
// turbo
```bash
echo "=== Strict TypeScript ===" && grep -E '"strict":\s*true' tsconfig.json 2>/dev/null && echo "STRICT MODE ENABLED" || echo "WARNING: Strict mode not enabled"
```
**Pass:** Strict mode must be enabled.

## 4.2 Content Schema Validation (P1)
// turbo
```bash
echo "=== Content Schema ===" && grep "defineCollection" src/content/config.ts 2>/dev/null | wc -l
```
**Pass:** Should show collections defined.

## 4.3 Console Logs (P3)
// turbo
```bash
echo "=== Console Logs ===" && grep -r "console.log" src/components src/pages --include="*.tsx" --include="*.astro" --include="*.ts" 2>/dev/null | wc -l
```
**Pass:** 0 in production code.

## 4.4 Security Vulnerabilities (P1)
// turbo
```bash
echo "=== Security Audit ===" && pnpm audit 2>&1 | grep -E "critical|high" | head -5
```
**Pass:** 0 critical/high vulnerabilities.

## 4.5 Exposed Secrets Check (P0)
// turbo
```bash
echo "=== Exposed Secrets ===" && grep -rE "API_KEY=|SECRET=|PASSWORD=|sk-|pk_live" src/ --include="*.ts" --include="*.tsx" --include="*.astro" 2>/dev/null | wc -l
```
**Pass:** 0.

## 4.6 Logic Verification (P0)
// turbo
```bash
echo "=== Unit Tests ===" && npx vitest run
```
**Pass:** All tests passed.

---

# PHASE 5: SEO & DISCOVERABILITY

## 5.1 robots.txt Exists (P0)
// turbo
```bash
echo "=== robots.txt ===" && ls -la public/robots.txt 2>/dev/null || echo "MISSING"
```
**Pass:** File exists.

## 5.2 Canonical URLs (P1)
// turbo
```bash
echo "=== Canonical URLs ===" && grep -r 'rel="canonical"' src/layouts/ 2>/dev/null | wc -l
```
**Pass:** Should be present in BaseLayout.

## 5.3 OG Images (P1)
// turbo
```bash
echo "=== OG Image ===" && grep -r "og:image" src/layouts/ 2>/dev/null | wc -l
```
**Pass:** Should be present.

## 5.4 Missing Meta Descriptions (P1)
// turbo
```bash
echo "=== Missing Descriptions ===" && grep -L "^description:" src/content/blog/*.md src/content/learn/*.md 2>/dev/null | wc -l
```
**Pass:** 0.

## 5.5 Broken Internal Links (P0)
// turbo
```bash
echo "=== Broken Learn Links ===" && grep -roP '\\]\\(/learn/[^)]+\\)' src/content/ 2>/dev/null | sed 's/.*\\/learn\\///' | sed 's/).*//' | sort -u | while read slug; do [ ! -f "src/content/learn/${slug}.md" ] && echo "BROKEN: $slug"; done
```
**Pass:** 0 broken links.

---

# PHASE 6: PERFORMANCE (Speed = Trust)

## 6.1 Large Assets (P1)
// turbo
```bash
echo "=== Large Assets (>500KB) ===" && find public src/assets -type f -size +500k 2>/dev/null | head -10
```
**Pass:** Minimal large files.

## 6.2 Bundle Size Check
```bash
pnpm run build 2>&1 | grep -E "kB|MB" | tail -20
```
**Pass:** JS bundles should be small (static site).

## 6.3 Image Optimization (P2)
// turbo
```bash
echo "=== Unoptimized Images ===" && find public -name "*.png" -size +100k 2>/dev/null | wc -l
```
**Pass:** Consider converting large PNGs to WebP.

## 6.4 Blocking External Assets (P0)
// turbo
```bash
echo "=== Blocking External CSS/JS ===" && grep -rE '<link.*href="http|<script.*src="http' src/layouts/ src/components/ | grep -v "nikhilpadala.com" | grep -v "dns-prefetch" | grep -v "preconnect" | wc -l
```
**Pass:** 0. Self-host critical assets (fonts, katex) to avoid external waterfalls.

## 6.5 Cache Configuration (P1)
// turbo
```bash
echo "=== Cache Headers ===" && grep "Cache-Control" vercel.json 2>/dev/null | wc -l
```
**Pass:** > 0. Must define cache rules for stats assets.

## 6.6 Mobile Layout Safety (P1)
// turbo
```bash
echo "=== Mobile Wrap Checks ===" && grep -r "flex-wrap" src/components/infographics 2>/dev/null | wc -l
```
**Pass:** > 0. Infographics must use `flex-wrap` for stats containers to avoid overflow.

---

# PHASE 7: ACCESSIBILITY

## 7.1 Missing Alt Text (P1)
// turbo
```bash
echo "=== Missing Alt Text ===" && grep -rn "<img" src/ --include="*.astro" --include="*.tsx" 2>/dev/null | grep -v "alt=" | wc -l
```
**Pass:** 0.

## 7.2 Interactive Without Hydration (P2)
// turbo
```bash
echo "=== React without client directive ===" && grep -l "useState\|onClick" src/components/*.tsx 2>/dev/null | while read f; do name=$(basename "$f" .tsx); grep -rq "client:.*$name" src/ || echo "NEEDS HYDRATION: $name"; done
```
**Pass:** All interactive components have client directives.

## 7.3 Dark Mode Hardcoded Colors (P1)
// turbo
```bash
echo "=== Hardcoded Slate (Dark Mode Issues) ===" && grep -rn "bg-slate-50\|bg-white\|text-slate-800\|text-slate-900" src/pages/*.astro src/pages/**/*.astro 2>/dev/null | wc -l
```
**Pass:** 0. Use theme variables (bg-bg-secondary, text-text-primary) instead.

---

# PHASE 8: RESEARCH STANDARDS (Architecture Integrity)

## 8.1 Research Console Compliance (P0)
// turbo
```bash
echo "=== Research Console Compliance ===" && find src/components/infographics -name "*.astro" ! -name "ResearchConsole.astro" -exec grep -L "ResearchConsole" {} \; | wc -l
```
**Pass:** 0. All infographic components must use the standard `ResearchConsole` shell.

---

# PHASE 9: BUILD VERIFICATION

## 8.1 Clean Build (P0)
```bash
rm -rf dist .vercel/output && pnpm run build
```
**Pass:** Build completes without errors.

---

# QUICK SUMMARY COMMAND
// turbo
```bash
echo "╔══════════════════════════════════════════════════╗"
echo "║           FULL SITE AUDIT SUMMARY                ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║ Em dashes:        $(grep -rn ' - \|-' src/content/**/*.md 2>/dev/null | wc -l | tr -d ' ') (target: 0)"
echo "║ Banned words:     $(grep -rni 'game-changing\|seamless\|cutting-edge' src/content/ 2>/dev/null | wc -l | tr -d ' ') (target: 0)"
echo "║ Weak language:    $(grep -rni 'simply\|just a\|obviously' src/content/ 2>/dev/null | wc -l | tr -d ' ') (target: 0)"
echo "║ Missing CTAs:     $(grep -rL 'opportunities\|latency-audit' src/content/blog/*.md 2>/dev/null | wc -l | tr -d ' ') (target: 0)"
echo "║ Large assets:     $(find public -type f -size +500k 2>/dev/null | wc -l | tr -d ' ') (target: <5)"
echo "║ TypeScript errs:  $(npx astro check 2>&1 | grep -c 'error' || echo 0) (target: 0)"
echo "╚══════════════════════════════════════════════════╝"
```

---

# PASS CRITERIA TABLE

| Check | Severity | Target | Rationale |
|-------|----------|--------|-----------|
| Em dashes | P0 | 0 | Weakens technical prose |
| Banned words | P0 | 0 | Destroys B2B credibility |
| Weak language | P1 | 0 | Undermines authority |
| Template content | P0 | 0 | Generic = untrusted |
| Vague claims | P1 | 0 | Specific numbers build trust |
| Missing CTAs | P1 | 0 | Every post converts |
| TypeScript errors | P0 | 0 | Broken code = low quality |
| Security vulns | P1 | 0 critical | Client trust requirement |
| Build | P0 | Success | Non-negotiable |

---

# REMEDIATION PRIORITY

**P0 (Fix Immediately):**
- Em dashes, banned words, template content
- TypeScript errors, broken links
- Exposed secrets, build failures

**P1 (Fix This Sprint):**
- Weak language, vague claims
- Missing CTAs, security vulnerabilities
- SEO gaps (robots.txt, canonical, OG)

**P2 (Polish):**
- Internal link density
- Open loops / rabbit holes
- Image optimization

**P3 (Optimization):**
- Console logs
- Unused components
- Minor spacing issues
