# Contributing to LatencyScope

Thank you for your interest in contributing to LatencyScope! This guide will help you get started.

## Prerequisites

Before contributing, ensure you have:

- Linux system (Ubuntu 22.04+ recommended)
- Python 3.10+
- BCC installed (`sudo apt install python3-bpfcc`)
- Root access for testing

## Development Setup

```bash
# Clone the repository
git clone https://github.com/padalan/latencyscope.git
cd latencyscope

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/latencyscope

# Run specific test file
pytest tests/test_utils.py
```

**Note:** Some tests require root privileges to test eBPF functionality:

```bash
sudo pytest tests/test_integration.py
```

## Code Quality

We use the following tools:

```bash
# Format code
ruff format .

# Check linting
ruff check .

# Type checking
mypy src/latencyscope
```

All checks must pass before merging.

## Commit Messages

Use conventional commit format:

```
feat: add ARM64 support
fix: handle missing BTF gracefully
docs: update installation instructions
test: add integration tests for IRQ module
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit with conventional message
6. Push and create PR

## eBPF Code Guidelines

When modifying eBPF programs (embedded in Python modules):

1. **Keep probes minimal** — Every instruction adds overhead
2. **Use ring buffers** — Perf buffers work, but ring buffers are more efficient
3. **Test on multiple kernels** — BPF verifier differs between versions
4. **Document tracepoint assumptions** — Tracepoint formats can change

## Adding a New Module

1. Create `src/latencyscope/modules/your_module.py`
2. Define the BPF program as a string constant
3. Create result dataclass with `violations` field
4. Add event handling logic
5. Register in `profiler.py`
6. Add CLI option in `cli.py`
7. Add tests
8. Update documentation

## Questions?

Open an issue or reach out to [@padalan](https://github.com/padalan).

Thank you for contributing!
