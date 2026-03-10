<!--
  Sync Impact Report
  ==================
  Version change: N/A (initial) → 1.0.0
  Modified principles: N/A (initial ratification)
  Added sections:
    - Principle I: Code Quality
    - Principle II: Testing Standards
    - Principle III: User Experience Consistency
    - Principle IV: Performance Requirements
    - Section: Technical Constraints
    - Section: Development Workflow
    - Section: Governance
  Removed sections: None
  Templates requiring updates:
    - .specify/templates/plan-template.md ✅ No updates needed
      (Constitution Check section is dynamically filled; template
      already references constitution gates generically)
    - .specify/templates/spec-template.md ✅ No updates needed
      (Success criteria and requirements sections already align
      with UX, performance, and testing principles)
    - .specify/templates/tasks-template.md ✅ No updates needed
      (Phase structure supports test-first workflow and polish
      phase covers performance/UX/quality concerns)
    - .specify/templates/commands/*.md ✅ No command files exist
    - README.md ✅ No updates needed (no constitution references)
  Follow-up TODOs: None
-->

# bt-web-ui Constitution

## Core Principles

### I. Code Quality

All code committed to this project MUST meet the following standards:

- **Readability first**: Code MUST be self-documenting through clear
  naming, small focused functions, and explicit intent. Comments MUST
  explain *why*, never *what*.
- **Consistent style**: All source files MUST pass the project's
  configured linter and formatter before merge. No exceptions.
- **Type safety**: All code MUST use strict type checking where the
  language supports it. `any` types, implicit conversions, and
  untyped interfaces are prohibited unless explicitly justified in
  a code comment referencing this principle.
- **Single responsibility**: Each module, component, and function
  MUST have one clear purpose. If a module description requires
  "and", it MUST be split.
- **No dead code**: Unused imports, unreachable branches, commented-out
  code blocks, and placeholder implementations MUST be removed before
  merge.

**Rationale**: A Bluetooth pairing/connection management UI handles
real-time device state. Ambiguous or poorly structured code leads to
subtle state management bugs that are difficult to diagnose over
wireless interfaces.

### II. Testing Standards

All features MUST be verified through automated tests:

- **Test-first workflow**: For new features, acceptance test
  expectations MUST be defined before implementation begins. Tests
  MUST fail before implementation and pass after.
- **Coverage requirements**: Every user-facing behavior MUST have at
  least one corresponding test. Critical paths (device pairing,
  connection lifecycle, error recovery) MUST have both unit and
  integration tests.
- **Test isolation**: Each test MUST be independent and
  deterministic. Tests MUST NOT depend on execution order, shared
  mutable state, or external Bluetooth hardware availability.
- **Mocking boundaries**: Hardware and OS Bluetooth APIs MUST be
  mocked at a clearly defined boundary layer. Mock implementations
  MUST faithfully represent documented API behavior including error
  states.
- **Regression discipline**: Every bug fix MUST include a test that
  reproduces the original failure before applying the fix.

**Rationale**: Bluetooth interactions are inherently asynchronous
and hardware-dependent. Without rigorous test isolation and coverage,
regressions surface only during manual testing with physical devices,
which is slow and unreliable.

### III. User Experience Consistency

The interface MUST provide a predictable, coherent experience:

- **Design system adherence**: All UI components MUST use the
  project's established component library and design tokens. Custom
  styling is prohibited unless no existing component fits and the
  addition is documented as a new design system element.
- **Feedback on every action**: Every user action (scan, pair,
  connect, disconnect) MUST produce visible feedback within 200ms.
  Long-running operations MUST display progress or activity
  indicators.
- **Error communication**: Errors MUST be shown in plain language
  describing what happened and what the user can do next. Raw
  error codes or stack traces MUST NOT be displayed to users.
- **State visibility**: The current state of every known Bluetooth
  device (disconnected, pairing, connected, error) MUST be
  clearly indicated at all times. Stale state MUST be explicitly
  marked or refreshed automatically.
- **Responsive layout**: The interface MUST be usable on screen
  widths from 320px to 2560px without loss of functionality or
  broken layouts.

**Rationale**: Bluetooth pairing is already a frustrating
experience for most users. The UI must reduce confusion through
immediate feedback, clear device states, and consistent visual
language.

### IV. Performance Requirements

The application MUST meet these performance baselines:

- **Initial load**: Time to interactive MUST be under 3 seconds on
  a mid-range device over a standard broadband connection. Bundle
  size MUST be monitored and regressions exceeding 10% MUST be
  justified.
- **Render performance**: UI updates (device list changes, status
  transitions) MUST render within one animation frame (16ms).
  No user interaction MUST cause visible jank or dropped frames.
- **Bluetooth operation latency**: The UI layer MUST NOT add more
  than 50ms of overhead to any Bluetooth API call. Scanning,
  pairing, and connection requests MUST be dispatched
  asynchronously and never block the main thread.
- **Memory discipline**: The application MUST NOT exhibit
  unbounded memory growth during normal usage. Device list
  updates, repeated scan cycles, and connection/disconnection
  loops MUST NOT leak memory. This MUST be validated through
  profiling during development.
- **Graceful degradation**: When Bluetooth is unavailable or
  permissions are denied, the application MUST remain responsive
  and display clear guidance instead of entering an error state
  or hanging.

**Rationale**: This is a device management tool that users will
keep open during active Bluetooth configuration sessions. Poor
performance or memory leaks during sustained use directly
undermines the tool's utility.

## Technical Constraints

- **Web Bluetooth API**: The application targets the Web Bluetooth
  API. All Bluetooth interactions MUST go through a single
  abstraction layer to isolate the rest of the codebase from API
  specifics and browser compatibility differences.
- **Browser support**: The application MUST support the latest two
  stable versions of Chromium-based browsers (Chrome, Edge). Firefox
  and Safari support is desirable but not required due to Web
  Bluetooth API limitations.
- **No server-side dependencies for core functionality**: Scanning,
  pairing, and connection management MUST work entirely client-side
  via the Web Bluetooth API. A server MAY be used only for serving
  static assets and optional features (e.g., configuration backup).
- **Dependency minimalism**: New runtime dependencies MUST be
  justified in the PR description. Prefer platform APIs and small
  focused libraries over large frameworks for Bluetooth-specific
  logic.

## Development Workflow

- **Branch-per-feature**: All work MUST happen on feature branches.
  Direct commits to the main branch are prohibited.
- **Constitution compliance check**: Every PR MUST be reviewed
  against the applicable principles in this constitution. The PR
  description MUST note which principles were validated.
- **Code review required**: All changes MUST be reviewed by at
  least one person other than the author before merge.
- **Test gate**: The CI pipeline MUST run the full test suite.
  Merging with failing tests is prohibited.
- **Performance gate**: Bundle size and key performance metrics
  MUST be tracked in CI. Regressions exceeding defined thresholds
  MUST block merge until resolved or justified.

## Governance

This constitution is the authoritative source of project standards.
It supersedes informal conventions, PR comments, and ad-hoc
decisions when there is a conflict.

- **Amendments**: Any change to this constitution MUST be proposed
  as a dedicated PR with a clear rationale. The change MUST NOT be
  bundled with feature work. All active contributors MUST be given
  the opportunity to review.
- **Versioning**: This constitution follows semantic versioning.
  MAJOR increments for principle removals or incompatible
  redefinitions. MINOR increments for new principles or material
  expansions. PATCH increments for clarifications and wording
  fixes.
- **Compliance review**: At minimum, constitution compliance MUST
  be verified during code review. If automated checks can enforce
  a principle (linting, bundle size, test coverage), they SHOULD
  be implemented in CI.
- **Runtime guidance**: For day-to-day development patterns and
  conventions not covered here, refer to project documentation in
  the repository. This constitution defines *what* standards apply;
  project docs define *how* to meet them.

**Version**: 1.0.0 | **Ratified**: 2026-03-10 | **Last Amended**: 2026-03-10
