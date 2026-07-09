# Virtus Core Workspace Architecture Directive

## Status

This document defines the long-term architecture of Virtus Core Workspace.

This is **NOT** an implementation task.

Do **not** implement this vision automatically.
Do **not** expand the current development scope.

Mission 1, validated product slices, and the first paying customer remain the highest priorities.

**Stability:** Treat this document as frozen architecture guidance. Implement only through validated slices after Mission 1 gates — not by rewriting this doc.

**Related:** Product feeling → `docs/VIRTUS_CORE_NORTH_STAR_DIRECTIVE.md` · Commerce → `docs/VIRTUS_COMMERCE_DELIVERY_DIRECTIVE.md` · Agent rules → `docs/NEXT_DEVELOPMENT_DIRECTIVE.md` · Team model → `docs/DIGITAL_EMPLOYEE_STRATEGY.md` (Horizon)

---

# Core Principle

Customers do not receive access to the Virtus Core development environment.

Customers receive **their own Virtus Core Workspace**, adapted to their business, while the platform itself remains protected.

The customer develops their business **inside** Virtus Core.

The customer never develops or modifies Virtus Core itself.

---

# Three-Layer Architecture

```
Virtus Core Platform
        │
Customer Workspace
        │
Customer Project
```

---

## Layer 1 — Virtus Core Platform

**Owner:** Virtus Core.

**Purpose:** The permanent foundation of the platform.

Examples:

* platform architecture
* security
* licensing
* update system
* authentication
* synchronization
* AI orchestration
* platform services
* internal infrastructure

This layer is **immutable for customers**.

Neither users nor AI assistants may modify it.

If requested, Vector must explain that system components are protected.

Example:

> "I cannot modify the core platform or its security components."

---

## Layer 2 — Customer Workspace

**Owner:** Customer.

**Purpose:** The customer's business environment.

Examples:

* business workflows
* dashboards
* business modules
* AI Specialists
* UI configuration
* automation
* integrations
* internal processes

Vector may evolve this layer only within platform rules.

Changes follow:

```
Plan
↓
Draft
↓
Confirmation
↓
Apply
```

No silent modifications.

---

## Layer 3 — Customer Project

**Owner:** Customer.

**Purpose:** Products created inside the workspace.

Examples:

* websites
* applications
* AI systems
* games
* automation
* documentation
* marketing assets
* business resources

The customer owns these deliverables according to the Commerce Directive.

---

# Workspace Philosophy

Customers do not buy "AI".

Customers receive a professional workspace that continuously evolves with their business.

Workspace examples may include:

* Commerce Workspace
* Restaurant Workspace
* Legal Workspace
* Healthcare Workspace
* Manufacturing Workspace
* Education Workspace

These are specialized workspaces built on one secure platform.

---

# Project Evolution

The customer speaks naturally with Vector.

Examples:

* "Add a loyalty program."
* "Create an inventory module."
* "Add an employee dashboard."

Vector responds by:

1. Understanding the request.
2. Creating a proposal.
3. Showing a draft or preview.
4. Asking for confirmation.
5. Applying changes only after approval.

The customer evolves the project.

The platform remains protected.

---

# Security Principle

**AI never modifies the Virtus Core Platform.**

AI only operates inside explicitly permitted layers.

Forbidden examples include:

* disabling licensing
* accessing internal secrets
* changing platform security
* modifying update mechanisms
* altering authentication
* executing unrestricted system changes

Protected boundaries must never be bypassed.

---

# Update Philosophy

Platform updates improve:

* security
* performance
* platform capabilities
* AI infrastructure

Platform updates must **not** overwrite:

* customer projects
* workspace configuration
* customer data
* conversation history
* business processes

Updates should preserve continuity whenever technically possible.

---

# Continuity Principle

The customer should never feel a break in their work.

Examples:

```
Browser
↓
Desktop
↓
Mobile
↓
New Version
↓
Continue the same project
```

Vector should always understand where work previously stopped whenever technically possible.

---

# Subscription Philosophy

Subscriptions provide continuous evolution.

They do **not** unlock ownership.

Examples:

* improve existing systems
* add new business modules
* evolve workflows
* collaborate with AI Specialists
* receive platform improvements
* receive workspace enhancements

Purchased projects remain the customer's property.

---

# Trust Principle

Every workspace must reinforce trust through:

* Ownership
* Privacy
* Transparency
* Reliability
* Honesty

Vector should never promise capabilities that do not yet exist.

Current product capabilities must always be represented honestly.

---

# Scope Protection

This document defines future architecture.

It must not automatically generate implementation tasks.

Future work must always follow:

```
One validated slice
→ One USER CAN VERIFY
→ One isolated commit
→ Real user feedback
→ Next slice
```

Mission 1 always has priority over long-term vision.

**Cursor should treat this document as long-term architecture guidance, not as an immediate engineering task.**

---

# North Star Sentence

> **Virtus Core should grow together with the customer's business, while the platform itself remains stable, protected, and under the control of Virtus Core.**
