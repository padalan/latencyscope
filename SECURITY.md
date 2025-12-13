# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

LatencyScope runs with elevated privileges (CAP_BPF or root) to load eBPF programs. Security is critical.

### How to Report

**Do not open a public issue for security vulnerabilities.**

1. Email: security@nikhilpadala.com
2. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 1 week
- **Fix timeline**: Depends on severity
  - Critical: 24-48 hours
  - High: 1 week
  - Medium: 2 weeks
  - Low: Next release

### What to Expect

1. Confirmation of receipt
2. Assessment and severity classification
3. Fix development
4. Coordinated disclosure
5. Credit in release notes (unless you prefer anonymity)

## Security Design

### Privilege Model

LatencyScope requires elevated privileges to:
- Load eBPF programs into the kernel
- Attach to kernel tracepoints
- Access performance counters

We recommend running with `CAP_BPF` and `CAP_PERFMON` capabilities instead of full root when possible.

### eBPF Safety

All eBPF programs are:
- Verified by the kernel's eBPF verifier
- Read-only (no kernel state modification)
- Bounded (no infinite loops)
- Memory-safe (no out-of-bounds access)

### Data Handling

- No network connectivity required
- No data leaves the local machine
- Tracing data stored in user-specified locations only

## Best Practices for Users

1. **Run on trusted systems only** — eBPF has kernel access
2. **Use capabilities, not root** — Minimize privilege surface
3. **Verify binary checksums** — Ensure authentic binaries
4. **Keep updated** — Apply security patches promptly

## Scope

In scope:
- eBPF program vulnerabilities
- Privilege escalation
- Memory corruption
- Information disclosure

Out of scope:
- Issues requiring physical access
- Social engineering
- Denial of service (it's a profiling tool)

---

Thank you for helping keep LatencyScope secure.
