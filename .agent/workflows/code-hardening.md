# Code Hardening Workflow

**Goal:** Eliminate technical debt, ensure type safety, and verify core logic.

"Hardening" means moving your code from "It works for me" to "It cannot fail in production."

## 1. Type Safety (The Static Shield)
// turbo
```bash
echo "=== 1. Checking Type Errors ===" && npx astro check
```
**Task:** 
- Reduce the 22 existing errors to 0.
- Most are likely `null` checks (e.g., `document.getElementById` might return null).
- **Fix:** Use optional chaining (`?.`) or explicit guards (`if (!el) return;`).

## 2. Strict Configuration (The Contract)
Ensure `tsconfig.json` has:
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true
  }
}
```

## 3. Unit Testing (The Logic Verification)
// turbo
```bash
echo "=== 2. Running Logic Tests ===" && npx vitest run
```
**Task:**
- We have complex math in `AntifragileMEV` (Hedging logic, Inclusion probability).
- This logic should be extracted to a `.ts` file (e.g., `src/lib/mev-math.ts`) and tested via Vitest.
- Currently, it's buried in the `.astro` script tag (untestable).

## 4. Security Audit (The Gatekeeper)
// turbo
```bash
echo "=== 3. Scanning for vulnerabilities ===" && pnpm audit
```
**Task:**
- Identify known vulnerabilities in dependencies.
- Fix high-severity issues via `pnpm update`.

## 5. Execution Plan
1.  Run `@[/code-hardening]` to see the current error state.
2.  I will fix the TypeScript errors file-by-file.
3.  I will extract the math logic to a testable module.
4.  I will write a test spec for the MEV formulas.
