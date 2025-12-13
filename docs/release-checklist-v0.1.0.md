# LatencyScope v0.1.0 Release Checklist

## Pre-Release Validation

### Code Quality
- [ ] All tests pass: `cargo test`
- [ ] No clippy warnings: `cargo clippy -- -D warnings`
- [ ] Code formatted: `cargo fmt --check`
- [ ] Documentation builds: `cargo doc --no-deps`
- [ ] No unsafe code without justification

### Functionality
- [ ] All 5 modules compile and load eBPF programs
- [ ] Ring buffer events flow correctly
- [ ] HDRHistogram records all percentiles accurately
- [ ] TUI renders without artifacts
- [ ] Perfetto export opens in https://ui.perfetto.dev/
- [ ] PDF report generates correctly
- [ ] JSON output is valid and parseable

### Platform Testing
- [ ] Ubuntu 22.04 (kernel 5.15)
- [ ] Ubuntu 24.04 (kernel 6.5)
- [ ] AWS m6i.metal (Intel Ice Lake)
- [ ] AWS c6gn.metal (AMD if applicable)
- [ ] Local development VM

### Overhead Validation
- [ ] P99 overhead < 500 ns for all modules
- [ ] Benchmark script runs: `scripts/benchmark.sh`
- [ ] Results documented in README

### Security
- [ ] SECURITY.md reviewed and accurate
- [ ] No sensitive data in code or commits
- [ ] CAP_BPF privilege model documented

## Documentation

### Repository Files
- [x] README.md complete and accurate
- [x] CHANGELOG.md updated with v0.1.0 entries
- [x] CONTRIBUTING.md reviewed
- [x] LICENSE present (MIT)
- [x] SECURITY.md present

### User Documentation
- [ ] Installation instructions tested on fresh system
- [ ] Quick start guide verified
- [ ] CLI help text (`--help`) reviewed
- [ ] Man page generated (optional)

### Technical Documentation
- [ ] Architecture doc complete: `docs/architecture.md`
- [ ] Module docs: `docs/modules/*.md`
- [ ] Deployment guide: `docs/deployment.md`

## Build & Distribution

### Binary Builds
- [ ] x86_64-unknown-linux-gnu build
- [ ] x86_64-unknown-linux-musl build (static)
- [ ] Binary size acceptable (< 10 MB)
- [ ] Binary runs on clean Ubuntu 22.04

### Cargo.toml
- [ ] Version set to "0.1.0"
- [ ] All metadata fields populated
- [ ] Repository URL correct
- [ ] Categories and keywords appropriate

### GitHub Release
- [ ] Create release tag: `git tag -a v0.1.0 -m "v0.1.0"`
- [ ] Push tag: `git push origin v0.1.0`
- [ ] GitHub Release created with:
  - [ ] Changelog excerpt
  - [ ] Binary attachments
  - [ ] Source tarball
- [ ] Release notes reviewed

### crates.io (Optional for v0.1.0)
- [ ] `cargo publish --dry-run` succeeds
- [ ] Description and documentation URL set
- [ ] Consider waiting for v0.2.0 for crates.io

## Announcement

### Blog Post
- [x] Blog post written (5000+ words)
- [ ] Blog post reviewed for accuracy
- [ ] Code snippets in blog tested
- [ ] Screenshots/recordings created
- [ ] Published to nikhilpadala.com

### Social Media
- [ ] Twitter/X thread drafted
- [ ] LinkedIn post drafted
- [ ] HackerNews submission prepared
- [ ] Reddit (/r/rust, /r/algotrading) prepared

### Timing
- [ ] Coordinate blog + GitHub release + social
- [ ] Target weekday morning (Pacific Time)
- [ ] Monitor HN/Reddit in first 2 hours

## Post-Release

### Monitoring
- [ ] GitHub Issues monitored for first 48 hours
- [ ] GitHub Discussions monitored
- [ ] Twitter mentions tracked

### Quick Fixes (if needed)
- [ ] v0.1.1 process documented
- [ ] Known issues documented in README

### Analytics
- [ ] GitHub stars tracked
- [ ] Blog post views tracked
- [ ] Binary download counts tracked

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Author | Nikhil Padala | | |
| Reviewer | | | |

---

## Notes

_Use this space for any release-specific notes or reminders._
