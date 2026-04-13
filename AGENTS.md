# Repository Guidelines

This repository follows a **pragmatic functional programming style** with strong testing discipline. Use these conventions to keep structure, tooling, and contributions consistent as it grows.

---

## Project Structure & Module Organization

- `src/`: application code organized by architectural layer
  - `src/core/`: pure calculations and domain logic (no I/O imports)
  - `src/adapters/`: I/O boundaries (filesystem, network, DB, env)
  - `src/app/`: orchestration and wiring (compose adapters + core)
- `tests/`: mirrors `src/` layout; one test module per unit
  - `tests/unit/`: tests for pure calculations
  - `tests/contract/`: tests for adapters with fakes
  - `tests/features/`: BDD scenarios (*.feature files)
  - `tests/steps/`: BDD step implementations
- `scripts/`: developer utilities and one-off tasks
- `docs/`: user/developer documentation; `assets/`: static files
- `Makefile`: single entrypoint for common tasks

Example: `src/core/<domain>/`, `src/adapters/<service>/`, `tests/unit/<domain>/`

---

## Build, Test, and Development Commands

Prefer `Makefile` wrappers; keep underlying commands inside targets.

- `make setup`: install dependencies (e.g., `uv install`)
- `make run`: start the app or local server
- `make test`: run the full test suite with coverage
- `make test-single TEST=path/to/test_file.py`: run a single test file
- `make lint`: run linters; `make fmt`: auto-format code
- `make clean`: remove build/test artifacts

If a target is missing, add it and reference the underlying tool in `scripts/`.

---

## Functional Programming Principles

### 1) Actions / Calculations / Data (ACD) Separation

**Rule A1 — Classify each function:**

- **Action**: depends on *when* or *how many times* it's called (I/O, time, randomness, shared state, network, filesystem, DB, UI)
- **Calculation**: pure function from inputs to output (no I/O, no hidden state, same output for same inputs)
- **Data**: inert facts (dicts, tuples, frozen dataclasses). No behavior.

**Agent checklist:**
- [ ] Label modules with their primary role (core = calculations, adapters = actions)
- [ ] Extract calculation code out of actions
- [ ] Keep domain rules in **calculations** operating on **data**

**Example: Extract calculation from action**

```python
# BEFORE: Action mixing I/O with business rules
cart = {"items": [], "total": 0.0}  # global mutable state

def add_to_cart(product_id: str) -> None:  # ACTION
    price = CATALOG[product_id]["price"]  # implicit global
    cart["items"].append({"id": product_id, "price": price})  # mutation
    cart["total"] += price  # mutation
    print(f"Total: {cart['total']:.2f}")  # I/O

# AFTER: Pure calculations + thin action shell
def cart_total(items: list[dict]) -> float:  # CALCULATION
    return sum(i["price"] * i.get("qty", 1) for i in items)

def add_to_cart(product: dict, cart: dict, render_fn) -> dict:  # ACTION
    items = cart["items"] + [{"id": product["id"], "price": product["price"]}]
    total = cart_total(items)  # pure
    render_fn(total)  # effect at edge
    return {**cart, "items": items, "total": total}
```

---

### 2) Minimize Implicit Inputs & Outputs

**Rule M1 — No hidden dependencies.**

Avoid globals, singletons, implicit I/O. Pass in everything you use; return what you produce.

**Agent checklist:**
- [ ] Replace implicit inputs (globals, time, env) with **parameters**
- [ ] Replace implicit outputs (printing, logging) with **return values** or explicit callbacks
- [ ] Calculations must not read or write module globals

**Example: Make dependencies explicit**

```python
# BEFORE
TAX_RATE = 0.0825

def add_tax(subtotal: float) -> float:  # not pure (reads global)
    return subtotal * (1 + TAX_RATE)

# AFTER
def add_tax(subtotal: float, tax_rate: float) -> float:  # CALCULATION
    return subtotal * (1 + tax_rate)
```

---

### 3) Design by Pulling Things Apart

**Rule D1 — Small, single-purpose, composable functions.**

Refactor until each function expresses one level of detail.

**Smell: "Implicit argument in function name"**

If a function name bakes in a variant (e.g., `get_open_tickets`), express the varying part as an argument or replace the body with a callback.

```python
# BEFORE
def get_open_tickets(tickets: list[dict]) -> list[dict]:
    return [t for t in tickets if t["status"] == "OPEN"]

# AFTER (express implicit argument)
def filter_by_status(tickets: list[dict], status: str) -> list[dict]:
    return [t for t in tickets if t["status"] == status]

# OR (replace body with predicate)
from collections.abc import Callable

def filter_with(tickets: list[dict], predicate: Callable[[dict], bool]) -> list[dict]:
    return [t for t in tickets if predicate(t)]
```

---

### 4) Immutable Data & Copy-on-Write

**Rule I1 — Never mutate shared data in calculations.**

Use **copy-on-write**: return a new structure with the change applied.

```python
# CALCULATION (copy-on-write for dict)
def add_item(cart: dict, item: dict) -> dict:
    return {**cart, "items": cart["items"] + [item]}

# CALCULATION (copy-on-write for dataclass)
from dataclasses import dataclass, replace

@dataclass(frozen=True)
class Cart:
    items: tuple[dict, ...]

def add_item(cart: Cart, item: dict) -> Cart:
    return replace(cart, items=cart.items + (item,))
```

**Rule I2 — Defensive copying across trust boundaries.**

- **Outgoing**: copy before handing to untrusted code
- **Incoming**: copy data received from untrusted code

```python
import copy

def call_plugin(plugin, data: dict) -> dict:
    safe_out = copy.deepcopy(data)   # outgoing copy
    result = plugin.process(safe_out)
    return copy.deepcopy(result)     # incoming copy
```

**Agent checklist:**
- [ ] No in-place mutation in calculations
- [ ] Copy at boundaries with libraries, plugins, or callbacks
- [ ] Use `frozen=True` dataclasses for domain models

---

### 5) First-Class Functions & Functional Iteration

**Rule F1 — Prefer comprehensions / built-ins over manual loops when clearer.**

```python
# Good: comprehension
emails = [c["email"] for c in customers if len(c["orders"]) > 0]

# Good: built-in reduction
total = sum(item["price"] * item["qty"] for item in items)
```

**Rule F2 — Use `update` helper for nested dict updates.**

```python
def update(obj: dict, key: str, f: Callable) -> dict:
    """Apply function f to obj[key], return new dict."""
    return {**obj, key: f(obj[key])}

# Example: increment stock count
def inc_stock(product: dict) -> dict:
    return update(product, "stock", lambda x: x + 1)
```

**Rule F3 — Compose in small steps; name intermediate results for clarity.**

---

### 6) Working with Nested Data

**Rule N1 — Use small helpers for nested updates.**

```python
from collections.abc import Callable

def update_in(data: dict, path: list[str], f: Callable) -> dict:
    """
    Pure update for nested dicts.
    Example: update_in(cart, ["customer", "email"], str.upper)
    """
    if not path:
        return f(data)

    key, *rest = path
    return {**data, key: update_in(data[key], rest, f)}

# Usage
new_cart = update_in(cart, ["customer", "address", "city"], str.upper)
```

---

### 7) Stratified Design (Layers)

**Rule S1 — Four patterns for well-layered code:**

1. **Straightforward implementation** at a single level of detail
2. **Abstraction barrier** to hide representations (swap internals without ripple)
3. **Minimal interface**: small, complete, orthogonal set of operations
4. **Comfortable layers**: each layer reads at one level of detail

**Example: Abstraction barrier for shopping cart**

```python
# cart.py — minimal interface, representation hidden
from dataclasses import dataclass, replace

@dataclass(frozen=True)
class Line:
    id: str
    price: float
    qty: int

@dataclass(frozen=True)
class Cart:
    items: tuple[Line, ...]

def empty() -> Cart:
    return Cart(items=())

def add(cart: Cart, item: Line) -> Cart:
    return replace(cart, items=cart.items + (item,))

def remove(cart: Cart, id: str) -> Cart:
    return replace(cart, items=tuple(i for i in cart.items if i.id != id))

def total(cart: Cart) -> float:
    return sum(i.price * i.qty for i in cart.items)

# Callers depend on functions, not internal representation
```

---

### 8) Push Effects to the Edges (Pure Core / Impure Shell)

**Rule A2 — Domain logic is pure; adapters live at the perimeter.**

```python
# src/core/order.py (pure calculations)
from dataclasses import dataclass

@dataclass(frozen=True)
class Order:
    lines: tuple[tuple[float, int], ...]  # (price, qty)

def add_line(order: Order, line: tuple[float, int]) -> Order:
    return Order(lines=order.lines + (line,))

def subtotal(order: Order) -> float:
    return sum(price * qty for price, qty in order.lines)

def total(order: Order, tax_rate: float) -> float:
    return subtotal(order) * (1 + tax_rate)

# src/adapters/ui.py (action)
def render_total(amount: float) -> None:
    print(f"Total: {amount:.2f}")

# src/app/checkout.py (orchestration)
from src.core.order import Order, add_line, total
from src.adapters.ui import render_total

def checkout(order: Order, lines: list, tax_rate: float) -> Order:
    for line in lines:
        order = add_line(order, line)
    render_total(total(order, tax_rate))
    return order
```

---

### 9) Architecture Summary

**Layer organization:**

```
src/
├── core/           # Pure calculations, domain logic
│   └── orders.py   # No I/O imports, frozen dataclasses
├── adapters/       # I/O boundaries (DB, HTTP, FS, env)
│   ├── db.py
│   └── http.py
└── app/            # Orchestration, wiring adapters to core
    └── service.py
```

**Dependency flow:** `app` → `adapters` + `core`; `core` never imports from `adapters` or `app`.

---

## Testing Strategy: BDD + TDD

### Core Philosophy

**Test the pure core exhaustively; test actions via ports and fakes.**

- **Many** calculation tests (example-based + property-based)
- **Few** action tests (integration/contract with fakes)
- **Handful** of BDD scenarios for key user-visible behaviors

### When to Start with BDD vs TDD

**Start with BDD** (pytest-bdd) when:
- Requirement is user/business-visible (acceptance criteria)
- Behavior spans multiple steps, I/O, or services
- You need shared language and traceability from story to code

**Start with TDD** (pytest unit + Hypothesis) when:
- Implementing a single pure transformation or algorithm
- Boundary conditions and invariants dominate the risk
- You're carving out a calculation from a larger flow

**Switch freely**: From BDD scenario to TDD for next pure function; from TDD back to BDD to prove integration.

### Red-Green-Refactor with Functional Constraints

1. **Red**: Write next failing test
   - BDD: scenario describing business outcome
   - TDD: unit test for pure function's next example or property

2. **Green**: Implement minimal code in pure core first
   - Add pure function signature (inputs fully explicit)
   - No I/O, mutation, hidden globals, or time calls in core

3. **Refactor**:
   - Extract pure functions
   - Enforce immutability (frozen dataclasses)
   - Introduce ports/adapters for side effects and inject them

4. Wire actions to shell + add integration/contract tests

5. Add property tests after first green to lock invariants

### Testing Strategy by A/C/D

**Calculations (pure):**
- Example-based tests for known cases and edges
- Property-based tests (Hypothesis) for invariants
- Deterministic: pass in seeds/providers for randomness/time

```python
from dataclasses import dataclass, replace

@dataclass(frozen=True)
class Account:
    id: str
    balance: int  # cents

def deposit(acc: Account, amount: int) -> Account:
    assert amount > 0
    return replace(acc, balance=acc.balance + amount)

# Example-based test
def test_deposit_increases_balance():
    a = Account("a1", 100)
    result = deposit(a, 20)
    assert result.balance == 120
    assert a.balance == 100  # immutability preserved

# Property-based test
from hypothesis import given, strategies as st

@given(
    balance=st.integers(min_value=0, max_value=10**9),
    amount=st.integers(min_value=1, max_value=10**7),
)
def test_deposit_monotonic(balance, amount):
    a = Account("a1", balance)
    b = deposit(a, amount)
    assert b.balance == balance + amount
    assert b is not a  # new object
```

**Actions (I/O shell):**
- Contract tests against ports (same test for fake and real adapter)
- Integration tests with fakes (in-memory repo, tmp_path, freezegun)
- Verify correct calls with values produced by calculations

```python
from typing import Protocol

class Repo(Protocol):
    def load(self, id: str) -> Account: ...
    def save(self, account: Account) -> None: ...

def deposit_cmd(repo: Repo, id: str, amount: int) -> None:
    acc = repo.load(id)
    repo.save(deposit(acc, amount))

# Contract test with fake
class FakeRepo:
    def __init__(self):
        self.store = {"a1": Account("a1", 100)}
    def load(self, id): return self.store[id]
    def save(self, acc): self.store[acc.id] = acc

def test_deposit_cmd_saves_updated_account():
    repo = FakeRepo()
    deposit_cmd(repo, "a1", 20)
    assert repo.store["a1"].balance == 120
```

**Data (schemas/models):**
- Immutability tests
- Validation tests (invalid inputs raise)
- Round-trip tests (encode/decode are inverses)

### BDD Scenarios Drive Functional Design

**Map scenarios to transformations:**

```gherkin
# tests/features/deposit.feature
Feature: Depositing funds updates balance
  Scenario: Successful deposit
    Given an account with balance 100
    When I deposit 20
    Then the new balance is 120
```

**Steps call pure functions:**

```python
# tests/steps/deposit_steps.py
from pytest_bdd import given, when, then, scenario
from src.core.account import Account, deposit

@scenario("../features/deposit.feature", "Successful deposit")
def test_deposit():
    pass

@given("an account with balance 100", target_fixture="account")
def account_fixture():
    return Account(id="a1", balance=100)

@when("I deposit 20", target_fixture="result")
def deposit_20(account):
    return deposit(account, 20)

@then("the new balance is 120")
def check_balance(result):
    assert result.balance == 120
```

### Testing Tooling (Python)

- **pytest**: core test runner, fixtures, parametrize
- **pytest-bdd**: BDD scenarios in Gherkin (optional but recommended for acceptance tests)
- **hypothesis**: property-based tests for calculations
- **freezegun**: deterministic time in tests
- **respx/httpx**: HTTP mocking
- **tmp_path**: filesystem isolation

### Agent Decision Checklist

Before writing code:

- [ ] Is requirement user/business-visible? → Start BDD scenario
- [ ] Is task a single pure transformation? → Start TDD unit test
- [ ] Is there I/O? → Define port (Protocol), write contract test with fake
- [ ] Are there clear invariants? → Add property test after first green
- [ ] Switch when uncertain: start TDD for smallest pure slice, add BDD when integration appears

### Coverage Target

- ≥80% line coverage overall
- 100% coverage for core calculations
- Add regression tests for every bug fix

---

## Coding Style & Naming Conventions

### Functional Style

1. **Approach with functional mindset:**
   - Use pure functions that don't modify global state
   - Prefer immutable data structures
   - Use higher-order functions and comprehensions where appropriate

2. **Keep code simple and minimalistic:**
   - Minimum lines necessary
   - Use built-in functions and standard library
   - Avoid unnecessary abstractions

3. **Avoid classes** (except when necessary):
   - Use functions and closures to organize code
   - Thin adapters required by frameworks (FastAPI, click) are OK but keep stateless
   - Prefer `@dataclass(frozen=True)` for data holders

4. **Avoid recursion** — use loops or comprehensions instead

5. **Plan before coding:**
   - Break problem into smaller steps
   - Identify core functions needed
   - Consider data flow through program

6. **Code guidelines:**
   - Descriptive but concise names
   - Type hints everywhere
   - Minimal inline comments (code should be self-documenting)

### Style Rules

- **Indentation**: 4 spaces; **line length**: 79 characters
- **Names**:
  - `snake_case`: files, modules, functions, variables
  - `PascalCase`: classes (when necessary)
  - `UPPER_SNAKE`: constants
  - `kebab-case`: docs/assets
- **Formatter/Linter**: Ruff for Python; Prettier + ESLint for JS/TS
- **Never use emojis** in code or documentation

### Comment Guidelines

1. Write docstring at top of each module explaining purpose
2. Include docstring for each function (what it does, parameters, returns)
3. Use inline comments sparingly, only for complex logic
4. Keep comments up-to-date with code

### Performance Pragmatism

- Start with immutable, simple copies
- If profiling shows hotspots, allow local mutation inside a function with clear boundaries (document with comment)
- Prefer built-in algorithms and libraries
- Avoid premature micro-optimizations

---

## Refactoring Moves

Keep these patterns handy:

- **Extract Calculation** (from an action)
- **Express Implicit Argument** (constant → parameter)
- **Replace Body with Callback** (give variation to higher-order function)
- **Replace Get-Modify-Set with `update`** (for dicts/nested data)
- **Introduce Copy-on-Write** (for lists/dicts/tuples)
- **Introduce Abstraction Barrier** (module with minimal interface)

---

## Package & Environment Management

- **Always use `uv`** for Python package management
- **Never use `pip` or `conda`**
- Environment in `.venv`; dependencies in `pyproject.toml`

---

## Commit & Pull Request Guidelines

- **Use Conventional Commits**: `type(scope): short summary`
  - Example: `feat(api): add query handler`
- **PRs include**:
  - Purpose and scope
  - Linked issues
  - Test plan/steps
  - Screenshots or logs for UI/CLI changes
  - Docs/CHANGELOG updates
  - New/updated tests

---

## Security & Configuration

- **Never commit secrets**; use `.env` for local, `.env.example` for required keys
- Validate inputs and handle errors defensively
- Document required environment variables in README
- Keep safe defaults

---

## Agent Workflow Summary

When implementing a feature:

1. **Classify**: Action / Calculation / Data?
2. **Choose test approach**: BDD for user behavior, TDD for pure logic
3. **Write failing test** (red)
4. **Implement pure core** (green) — no I/O, explicit inputs, immutable
5. **Refactor** — extract calculations, enforce immutability, add types
6. **Wire to shell** — inject adapters via ports
7. **Add property tests** — lock down invariants
8. **Verify**: `make test`, `make lint`, check coverage
9. **Commit**: conventional commit message

---

## End-to-End Example

```python
# src/core/order.py — PURE CALCULATIONS
from dataclasses import dataclass

@dataclass(frozen=True)
class Line:
    price: float
    qty: int

@dataclass(frozen=True)
class Order:
    lines: tuple[Line, ...]

def new_order() -> Order:
    return Order(lines=())

def add_line(order: Order, line: Line) -> Order:
    return Order(lines=order.lines + (line,))

def subtotal(order: Order) -> float:
    return sum(l.price * l.qty for l in order.lines)

def total(order: Order, tax_rate: float) -> float:
    return subtotal(order) * (1 + tax_rate)

# src/adapters/env.py — ACTION
def read_tax_rate(env: dict) -> float:
    return env.get("tax_rate", 0.0)

# src/adapters/ui.py — ACTION
def render_total(amount: float) -> None:
    print(f"Total: {amount:.2f}")

# src/app/checkout.py — ORCHESTRATION (thin action)
from src.core.order import Order, add_line, total, new_order, Line
from src.adapters.env import read_tax_rate
from src.adapters.ui import render_total

def checkout(env: dict, lines: list[Line]) -> Order:
    order = new_order()
    for line in lines:
        order = add_line(order, line)
    amount = total(order, read_tax_rate(env))
    render_total(amount)
    return order

# tests/unit/test_order.py — TDD TESTS
from src.core.order import Order, Line, add_line, subtotal, total

def test_subtotal():
    o = Order(lines=(Line(10.0, 2), Line(3.0, 5)))
    assert subtotal(o) == 10.0 * 2 + 3.0 * 5

def test_total_with_tax():
    o = Order(lines=(Line(10.0, 2),))
    assert total(o, 0.1) == 10.0 * 2 * 1.1

# tests/features/checkout.feature — BDD SCENARIO
Feature: Checkout calculates total with tax
  Scenario: Order with two items
    Given an empty order
    When I add items worth 35
    Then the total with 10% tax is 38.5

# tests/steps/checkout_steps.py
from pytest_bdd import given, when, then, scenario
from src.core.order import new_order, add_line, total, Line

@scenario("../features/checkout.feature", "Order with two items")
def test_checkout():
    pass

@given("an empty order", target_fixture="order")
def empty_order():
    return new_order()

@when("I add items worth 35", target_fixture="order")
def add_items(order):
    return add_line(add_line(order, Line(10, 2)), Line(3, 5))

@then("the total with 10% tax is 38.5")
def check_total(order):
    assert total(order, 0.1) == 38.5
```

---

