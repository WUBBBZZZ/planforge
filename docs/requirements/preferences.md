# User preferences (display and UX)

Preferences affect layout and navigation. They do **not** change planner
semantics the way [configurable-policies.md](configurable-policies.md) do.

Store alongside policies in settings; validate keys server-side.

## Accepted defaults (2026-07-22)

### `app.default_landing_view`

| Option | Behavior |
|--------|----------|
| `week` | Open to Week view after launch |
| `today` | Open to Today view |
| `month` | Open to Month view (post-MVP) |

**Default:** `week` — **accepted**

Rationale: planning-first workflow; Today remains one click away in nav.

### `capture.entry_style`

| Option | Behavior |
|--------|----------|
| `modal` | Capture form in a dialog overlay |
| `page` | Dedicated capture route |
| `inline` | Inline panel on current view |

**Default:** `modal` — **likely** (provisional until Slice 2 capture UI is built)

Rationale: fast capture without leaving Week context; confirm during implementation.

## Related display preferences (existing)

### `week.start_day`

See policy `week.start_day` — default **Monday** (ADR 0006).

### Theme

In-memory during infrastructure phases; persistence deferred to offline security gate.
