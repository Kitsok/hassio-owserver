# Tests

## Prerequisites

- Python 3.10+
- Docker with Compose plugin
- `yq` (YAML processor)

## Install dependencies

```bash
pip install -r tests/requirements.txt
```

## Run all tests

```bash
pytest tests/ -v --tb=short
```

Each run builds `local/owserver:ci` through Docker Compose so local changes
are tested. Docker still reuses unchanged build layers. CI explicitly sets
`OWSERVER_TEST_REUSE_IMAGE=1` to test the image built in its preceding step.
Set that variable locally only when intentionally testing a prebuilt image.

## Environment variables

Tests detect the target platform automatically. To override (e.g. in CI):

```bash
BUILD_PLATFORM=linux/amd64 BUILD_ARCH=amd64 pytest tests/ -v --tb=short
```

| Variable | Default | Description |
|---|---|---|
| `BUILD_PLATFORM` | `linux/arm64` | Docker platform for the container |
| `BUILD_ARCH` | `aarch64` | Build architecture passed to Dockerfile |

## Test files

| File | Description |
|---|---|
| `test_integration.py` | End-to-end tests against running owserver container (owdir, owread, owhttpd) |
| `test_template.py` | Template rendering tests for `owfs.template.conf` (device types, temperature scales) |
| `test_validation.py` | Config validation tests (missing required fields, deprecation warnings) |
| `conftest.py` | Shared fixtures: docker compose lifecycle, template rendering helpers |

## Cleanup

```bash
make clean
```
