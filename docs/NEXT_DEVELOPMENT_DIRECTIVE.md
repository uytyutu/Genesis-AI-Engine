# Next Development Directive

**For Cursor and all agents working on Virtus Core / Genesis.**

Think as a **product architect**, not as a programmer of isolated features.

---

## Read First

Before proposing or implementing any product changes, read and fully understand:

* `docs/VIRTUS_CORE_NORTH_STAR_DIRECTIVE.md`
* `docs/VIRTUS_COMMERCE_DELIVERY_DIRECTIVE.md`
* `docs/DIGITAL_EMPLOYEE_STRATEGY.md`
* `docs/NORTH_STAR.md`

These documents are **frozen product philosophy**.

Do **not** rewrite them.
Do **not** extend them.
Do **not** reinterpret them.

Treat them as long-term product vision.

---

## Current Development Stage

The vision phase is complete.

Do **not** propose new philosophy documents.
Do **not** propose new long-term strategy.
Do **not** expand North Star.

Focus entirely on **validated product implementation**.

---

## Development Rules

For every future proposal ask yourself:

1. Does this move Virtus Core closer to Mission 1?
2. Does this make Virtus Core more enjoyable to use?
3. Does this simplify the user's journey?
4. Can this be implemented as **one small validated slice**?
5. Can this slice be **reverted independently**?

If any answer is **No**, stop and propose a smaller slice.

---

## Important — Do Not Auto-Implement

Do **NOT** implement any part of the Commerce & Delivery vision automatically.

This includes, but is not limited to:

* Payment Hub
* Publishing workflow
* Domain registration
* Hosting automation
* Subscription system
* Project lifecycle automation
* Co-Creation Workspace
* Project Director
* Digital Specialists orchestration

These are long-term product directions.

They are implemented **only after explicit approval from the CEO**.

---

## Current Product Model

Virtus Core currently operates using the **existing delivery model**.

Do **not** replace existing ordering, payment, delivery, or timeline flows with the future Co-Creation model unless explicitly requested by the CEO.

| Layer | Rule |
|-------|------|
| **Vision** | Long-term orienting star — guides *future* slices |
| **Code** | Today's honest reality — what users can verify *now* |

Future vision guides future implementation.

Current product must **always honestly represent its current capabilities**.

**Never promise functionality that has not yet been implemented.**

When the CEO says **«Открываем Co-Creation»** — read the frozen directives and implement **one small slice at a time**, not the full workspace.

---

## Current Priority

Mission 1 remains the highest priority.

Every implementation must help reach:

* First real customer
* First real payment
* First successful delivery

---

## Product Thinking

When suggesting future work, think in this order:

```
1. Real customer problem
2. Smallest useful solution
3. USER CAN VERIFY
4. Tests
5. Commit
6. Real usage
7. Feedback
8. Next slice
```

Never jump directly to large implementations.

---

## Current Question

Before proposing any code changes, ask:

> **What is the single smallest slice that creates the biggest value for the next real customer?**

Build only that.

Everything else stays as vision until requested by the CEO.

---

## Agent Discipline (summary)

* One heavy build per turn — see `.cursor/rules/cursor-stability.mdc`
* Philosophy frozen — slices only
* Vision ≠ today's product
* CEO gates: Co-Creation, Commerce, Payment Hub, Specialists

**Cursor should treat this document as active development guidance until Mission 1 is proven.**
