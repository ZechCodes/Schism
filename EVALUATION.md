# Schism Project Evaluation

## Overview

**Schism** (v0.2.0b1) is a Python service framework for autowiring that allows applications to
run as either monolithic single-process apps or distributed microservices with minimal code
changes. It uses Bevy for dependency injection and provides a bridge abstraction layer for
inter-service communication.

---

## Critical Issues (Project Non-Functional)

### 1. Bevy API Incompatibility - Module Cannot Be Imported

**Severity: Blocker**

The project cannot be imported at all. Running `import schism` immediately fails:

```
ImportError: cannot import name 'Repository' from 'bevy'
```

The codebase was written against an older Bevy 3.x beta API that used `Repository`, but the
locked dependency (bevy 3.0.0b2) has renamed these to `Container`/`Registry`:

| Code Uses (broken)         | Bevy 3.0.0b2 Equivalent  |
|---------------------------|--------------------------|
| `Repository`              | `Container` + `Registry` |
| `Repository.factory()`   | `Registry().create_container()` |
| `Repository.set_repository()` | `global_container` context var |
| `Repository.get_repository()` | `get_container()` |
| `get_repository()`        | `get_container()`        |

**Affected files:**
- `schism/services.py:3` - `from bevy import Repository`
- `schism/controllers.py:37` - uses `bevy.get_repository()`
- `schism/bridges.py:31` - `from bevy import get_repository`
- `tests/conftest.py:1` - `from bevy import Repository`
- `tests/service_test.py` - indirectly via Service base class

**Result:** Zero tests pass. The project is entirely non-functional.

### 2. All Tests Fail

Because the module cannot be imported, all tests fail with `ImportError`:

```
$ uv run pytest tests/ -v
ImportError while loading conftest 'tests/conftest.py'.
E   ImportError: cannot import name 'Repository' from 'bevy'
```

---

## Significant Bugs

### 3. Sequential Task Execution in `_run_tasks`

**File:** `schism/controllers.py:142-145`

```python
async def _run_tasks(self):
    async with asyncio.TaskGroup() as group:
        for task in self._launch_tasks:
            await group.create_task(task)
```

`TaskGroup.create_task()` returns an `asyncio.Task` (not a coroutine). Awaiting it blocks until
that task completes before the next is created, making all launch tasks run **sequentially**
instead of concurrently. The `await` keyword should be removed:

```python
group.create_task(task)
```

This bug means that in distributed mode, bridge servers would start one at a time rather than
concurrently, and a long-running task would block subsequent tasks from starting.

### 4. Demo Middleware Uses Non-Existent API

**File:** `demos/greetings/greetings.py:26-47`

The `MiddlewareExample` class defines methods that don't exist in the `Middleware` ABC:
- `filter_client_call`
- `filter_client_result`
- `filter_server_call`
- `filter_server_result`

The actual `Middleware` base class requires a single `run(self, payload)` method. This demo
middleware would be silently ignored (the base `run` method is abstract, so instantiation would
fail). The demo is non-functional in distributed mode with middleware enabled.

### 5. Typo in Method Names: `udpate_a` / `udpate_b`

**Files:** `tests/service_test.py:32,36` and `tests/test_service_integration.py:41-42`

Methods are named `udpate_a` and `udpate_b` instead of `update_a` and `update_b`. While
internally consistent (tests call the misspelled name), this would confuse users looking at tests
as examples.

---

## Architectural and Design Observations

### 6. Security Concern: Pickle-Based Serialization

**File:** `schism/ext/bridges/simple_tcp.py`

The TCP bridge uses Python `pickle` for serialization, which is inherently unsafe. While the
SHA256 signature provides some protection against tampering, the default secret key is an empty
string (`os.environ.get("SCHISM_TCP_BRIDGE_SECRET", "")`). Any attacker who knows the empty
default can craft valid signed payloads for arbitrary code execution.

The documentation describes this as "somewhat secure" which is accurate but understated for a
framework that may be used in production.

### 7. No CI for Tests

**File:** `.github/workflows/publish.yaml`

The only CI pipeline publishes to PyPI on release. There is no workflow for:
- Running tests on PRs or pushes
- Linting or type checking
- Testing across Python versions

This means broken code (like the current bevy incompatibility) can be released without automated
detection.

### 8. Build System Mismatch

The CI/CD pipeline uses **Poetry** (`snok/install-poetry@v1`, `poetry build`, `poetry publish`),
but the project is configured with `pyproject.toml` standard format and uses **uv** for
dependency locking (`uv.lock`). The `pyproject.toml` has no `[tool.poetry]` section or
`[build-system]` table, which means `poetry build` may not work correctly.

### 9. `pyproject.toml` Missing `[project.scripts]` Entry Point

The CLI entry point `schism` is referenced in the README and demo documentation but is not
defined in `pyproject.toml`. There is no `[project.scripts]` section:

```toml
[project.scripts]
schism = "schism.cli_script:run"
```

Without this, `pip install schism` would not create the `schism` CLI command.

---

## Code Quality Assessment

### Strengths
- Clean architecture with clear separation of concerns (services, bridges, controllers, middleware)
- Well-documented modules with thorough docstrings explaining design decisions
- Good use of Python pattern matching and type aliases
- Middleware system is elegantly designed with composable stack
- The monolith-to-microservice concept is well thought out
- Configuration system using nubby + pydantic is flexible

### Weaknesses
- Single bridge implementation (SimpleTCP only)
- No input validation on bridge payloads beyond signature checking
- No retry logic or connection pooling in the TCP client
- No graceful shutdown handling for bridge servers
- `lru_cache` on instance methods (`SimpleTCPClient.host`, `SimpleTCPServer.host/port`) creates
  a memory leak since `self` is part of the cache key and prevents garbage collection

---

## Test Coverage Assessment

### What's Tested
- Bridge client injection via Bevy DI (1 test)
- Bridge server creation and entry point registration (1 test)
- Middleware execution order for client and server contexts (1 test)
- End-to-end integration with real TCP bridge subprocesses (1 test)

### What's Not Tested
- `MonolithicController` (start_app flow)
- Configuration loading from YAML/JSON/TOML files
- Error propagation (RemoteError, exception payloads)
- `wait_for()` timeout behavior
- CLI argument parsing (`schism/run.py:main`)
- Edge cases: invalid configs, missing services, network failures
- Middleware with actual bridge communication
- `LaunchConfig` and `start_application` flow
- `BridgeServiceFacade.call_async_method` with invalid service types

**Total: 4 tests, none currently passing.**

---

## Summary

| Category | Status |
|----------|--------|
| Importable | No |
| Tests passing | 0/4 |
| Demo functional | No |
| CLI functional | No |
| Publishable to PyPI | No (build system mismatch) |
| Documentation | Adequate for beta |
| Architecture | Well-designed |
| Code quality | Good (modulo bugs above) |

**Overall Assessment:** The project has a solid architectural foundation and a clear, useful
concept. However, it is currently **non-functional** due to the bevy API incompatibility. The
locked dependency (bevy 3.0.0b2) does not provide the `Repository` class that the codebase
relies on throughout. Fixing this single dependency issue would likely restore basic
functionality, after which the sequential task execution bug and demo middleware API mismatch
should be addressed.
