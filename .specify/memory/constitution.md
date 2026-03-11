<!-- 
SYNC IMPACT REPORT
==================
Version Change: INIT → 1.0.0 (Initial Constitution)
Created: 2026-03-11
Principles Added: 5 core principles
Sections: Technology Stack, Development Workflow & Quality Gates
Dependencies: spec-template.md, plan-template.md, tasks-template.md (✅ reviewed)
No breaking changes; first version establishes baseline.
-->

# Anomaly Detector Constitution

## Core Principles

### I. Clean Architecture
Backend and frontend MUST strictly follow clean architecture patterns with clear separation of concerns. Backend: domain → use case → interface adapters → framework/database layers. Frontend: components → custom hooks → services → API clients. No business logic in presentation layers; circular dependencies prohibited.

### II. Quality-First Development
Every code change requires TDD discipline: write tests that fail → implement feature → refactor. Code review MUST verify unit test coverage (minimum 80% for changed files) and integration tests for API contracts. No production code merges without passing CI/CD gates. Linting and formatting (Python: ruff + black; JavaScript: ESLint + Prettier) MUST enforce consistency automatically.

### III. User-Centric Excellence
All features must be validated against user scenarios (acceptance criteria) before marking complete. Frontend MUST prioritize intuitive UX with clear feedback loops. Backend MUST provide comprehensive error messages and API response clarity. Performance metrics MUST be tracked: UI responsiveness (target <100ms interaction latency), API p95 latency, error resolution time.

### IV. Performance & Observability
Every new backend feature MUST include structured logging (correlation IDs, request tracing). Database queries MUST be indexed appropriately; N+1 query problems prohibited. Frontend MUST monitor bundle size (<500KB gzipped for initial load) and Core Web Vitals (LCP, FID, CLS). Anomaly detection accuracy MUST be continuously tracked with metrics dashboards.

### V. Dependency Management via UV
Python backend dependency management MUST use UV exclusively (no pip directly). Lock files MUST be committed (uv.lock). All transitive dependencies pinned for reproducible builds. Frontend dependencies managed via npm with package-lock.json committed. Dependencies updated monthly with security audit (govulncheck equivalent for JS).

## Technology Stack & Runtime Requirements

**Backend**:
- Python 3.12 with UV dependency manager
- Framework/Libraries: FastAPI (or equivalent for RESTful APIs)
- Database: PostgreSQL (if persistence needed) or SQLite for prototypes
- Testing: pytest with coverage reporting

**Frontend**:
- ReactJS (latest stable)
- Node.js v24.13 (minimum; prefer LTS if available)
- Build tooling: Vite or Webpack
- Testing: Vitest + React Testing Library

**Shared**:
- Version control: Git with main + feature branches
- Environment: Python 3.12, Node 24.13 explicitly pinned
- Monorepo structure: `/backend` for Python, `/frontend` for React

## Development Workflow & Quality Gates

**Code Review Requirements**:
- All PRs MUST have at least one approval before merge.
- Review checklist: (1) Tests pass locally, (2) Coverage meets threshold, (3) No console errors/warnings, (4) Architecture compliance verified, (5) Performance impact assessed.

**Testing Gates**:
- Unit tests REQUIRED for all business logic (target 80%+ coverage).
- Integration tests REQUIRED for API contracts and database interactions.
- Contract tests MUST validate backend-frontend API compatibility.
- No test skips (`.skip()`, `.only()`) in main branch.

**Quality Enforcement**:
- Pre-commit hooks MUST run linters and formatters (fail if violations detected).
- CI/CD pipeline fails on:
  - Test failures or coverage drops below 80%
  - Linting violations
  - Type checking errors (TypeScript/mypy)
  - Security vulnerabilities (snyk, bandit for Python)

## Governance

**Amendments**: Constitution changes require explicit documentation (reason + migration impact) and developer consensus. Version bumping follows semantic versioning: MAJOR (principle removal/redefinition), MINOR (new principle/section), PATCH (clarifications/typos).

**Compliance Verification**: All pull requests to main MUST declare which principle(s) they address. Complexity that violates principles requires explicit justification in PR description.

**Runtime Guidance**: See `.github/procedures.md` (if exists) or project README for development setup and daily workflow practices. This constitution is the source of truth for governance; procedures documents provide operational implementation specifics.

**Version**: 1.0.0 | **Ratified**: 2026-03-11 | **Last Amended**: 2026-03-11
