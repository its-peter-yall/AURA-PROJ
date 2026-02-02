# Project Workflow

**Version:** 2.0  
**Last Updated:** 2026-02-02  
**Project:** AURA Twin (AURA-CHAT + AURA-NOTES-MANAGER)

## Guiding Principles

1. **The Plan is the Source of Truth:** All work must be tracked in `plan.md`
2. **The Tech Stack is Deliberate:** Changes to the tech stack must be documented in `tech-stack.md` *before* implementation
3. **Test-Driven Development:** Write unit tests before implementing functionality
4. **High Code Coverage:** Aim for >80% code coverage for all modules
5. **User Experience First:** Every decision should prioritize user experience
6. **Non-Interactive & CI-Aware:** Prefer non-interactive commands. Use `CI=true` for watch-mode tools (tests, linters) to ensure single execution.

## Task Workflow

All tasks follow a strict lifecycle:

### Standard Task Workflow

1. **Select Task:** Choose the next available task from `plan.md` in sequential order

2. **Mark In Progress:** Before beginning work, edit `plan.md` and change the task from `[ ]` to `[~]`

3. **Write Failing Tests (Red Phase):**
   - Create a new test file for the feature or bug fix.
   - Write one or more unit tests that clearly define the expected behavior and acceptance criteria for the task.
   - **CRITICAL:** Run the tests and confirm that they fail as expected. This is the "Red" phase of TDD. Do not proceed until you have failing tests.

4. **Implement to Pass Tests (Green Phase):**
   - Write the minimum amount of application code necessary to make the failing tests pass.
   - Run the test suite again and confirm that all tests now pass. This is the "Green" phase.

5. **Refactor (Optional but Recommended):**
   - With the safety of passing tests, refactor the implementation code and the test code to improve clarity, remove duplication, and enhance performance without changing the external behavior.
   - Rerun tests to ensure they still pass after refactoring.

6. **Verify Coverage:** Run coverage reports using the project's chosen tools. For example, in a Python project, this might look like:
   ```bash
   pytest --cov=app --cov-report=html
   ```
   Target: >80% coverage for new code. The specific tools and commands will vary by language and framework.

7. **Document Deviations:** If implementation differs from tech stack:
   - **STOP** implementation
   - Update `tech-stack.md` with new design
   - Add dated note explaining the change
   - Resume implementation

8. **Commit Code Changes:**
   - Stage all code changes related to the task.
   - Propose a clear, concise commit message e.g, `feat(ui): Create basic HTML structure for calculator`.
   - Perform the commit.

9. **Attach Task Summary with Git Notes:**
   - **Step 9.1: Get Commit Hash:** Obtain the hash of the *just-completed commit* (`git log -1 --format="%H"`).
   - **Step 9.2: Draft Note Content:** Create a detailed summary for the completed task. This should include the task name, a summary of changes, a list of all created/modified files, and the core "why" for the change.
   - **Step 9.3: Attach Note:** Use the `git notes` command to attach the summary to the commit.
     ```bash
     # The note content from the previous step is passed via the -m flag.
     git notes add -m "<note content>" <commit_hash>
     ```

10. **Get and Record Task Commit SHA:**
    - **Step 10.1: Update Plan:** Read `plan.md`, find the line for the completed task, update its status from `[~]` to `[x]`, and append the first 7 characters of the *just-completed commit's* commit hash.
    - **Step 10.2: Write Plan:** Write the updated content back to `plan.md`.

11. **Commit Plan Update:**
    - **Action:** Stage the modified `plan.md` file.
    - **Action:** Commit this change with a descriptive message (e.g., `conductor(plan): Mark task 'Create user model' as complete`).

### Phase Completion Verification and Checkpointing Protocol

**Trigger:** This protocol is executed immediately after a task is completed that also concludes a phase in `plan.md`.

1.  **Announce Protocol Start:** Inform the user that the phase is complete and the verification and checkpointing protocol has begun.

2.  **Ensure Test Coverage for Phase Changes:**
    -   **Step 2.1: Determine Phase Scope:** To identify the files changed in this phase, you must first find the starting point. Read `plan.md` to find the Git commit SHA of the *previous* phase's checkpoint. If no previous checkpoint exists, the scope is all changes since the first commit.
    -   **Step 2.2: List Changed Files:** Execute `git diff --name-only <previous_checkpoint_sha> HEAD` to get a precise list of all files modified during this phase.
    -   **Step 2.3: Verify and Create Tests:** For each file in the list:
        -   **CRITICAL:** First, check its extension. Exclude non-code files (e.g., `.json`, `.md`, `.yaml`).
        -   For each remaining code file, verify a corresponding test file exists.
        -   If a test file is missing, you **must** create one. Before writing the test, **first, analyze other test files in the repository to determine the correct naming convention and testing style.** The new tests **must** validate the functionality described in this phase's tasks (`plan.md`).

3.  **Execute Automated Tests with Proactive Debugging:**
    -   Before execution, you **must** announce the exact shell command you will use to run the tests.
    -   **Example Announcement:** "I will now run the automated test suite to verify the phase. **Command:** `CI=true npm test`"
    -   Execute the announced command.
    -   If tests fail, you **must** inform the user and begin debugging. You may attempt to propose a fix a **maximum of two times**. If the tests still fail after your second proposed fix, you **must stop**, report the persistent failure, and ask the user for guidance.

4.  **Propose a Detailed, Actionable Manual Verification Plan:**
    -   **CRITICAL:** To generate the plan, first analyze `product.md`, `product-guidelines.md`, and `plan.md` to determine the user-facing goals of the completed phase.
    -   You **must** generate a step-by-step plan that walks the user through the verification process, including any necessary commands and specific, expected outcomes.
    -   The plan you present to the user **must** follow this format:

        **For a Frontend Change:**
        ```
        The automated tests have passed. For manual verification, please follow these steps:

        **Manual Verification Steps:**
        1.  **Start the development server with the command:** `npm run dev`
        2.  **Open your browser to:** `http://localhost:3000`
        3.  **Confirm that you see:** The new user profile page, with the user's name and email displayed correctly.
        ```

        **For a Backend Change:**
        ```
        The automated tests have passed. For manual verification, please follow these steps:

        **Manual Verification Steps:**
        1.  **Ensure the server is running.**
        2.  **Execute the following command in your terminal:** `curl -X POST http://localhost:8080/api/v1/users -d '{"name": "test"}'`
        3.  **Confirm that you receive:** A JSON response with a status of `201 Created`.
        ```

5.  **Await Explicit User Feedback:**
    -   After presenting the detailed plan, ask the user for confirmation: "**Does this meet your expectations? Please confirm with yes or provide feedback on what needs to be changed.**"
    -   **PAUSE** and await the user's response. Do not proceed without an explicit yes or confirmation.

6.  **Create Checkpoint Commit:**
    -   Stage all changes. If no changes occurred in this step, proceed with an empty commit.
    -   Perform the commit with a clear and concise message (e.g., `conductor(checkpoint): Checkpoint end of Phase X`).

7.  **Attach Auditable Verification Report using Git Notes:**
    -   **Step 7.1: Draft Note Content:** Create a detailed verification report including the automated test command, the manual verification steps, and the user's confirmation.
    -   **Step 7.2: Attach Note:** Use the `git notes` command and the full commit hash from the previous step to attach the full report to the checkpoint commit.

8.  **Get and Record Phase Checkpoint SHA:**
    -   **Step 8.1: Get Commit Hash:** Obtain the hash of the *just-created checkpoint commit* (`git log -1 --format="%H"`).
    -   **Step 8.2: Update Plan:** Read `plan.md`, find the heading for the completed phase, and append the first 7 characters of the commit hash in the format `[checkpoint: <sha>]`.
    -   **Step 8.3: Write Plan:** Write the updated content back to `plan.md`.

9. **Commit Plan Update:**
    - **Action:** Stage the modified `plan.md` file.
    - **Action:** Commit this change with a descriptive message following the format `conductor(plan): Mark phase '<PHASE NAME>' as complete`.

10.  **Announce Completion:** Inform the user that the phase is complete and the checkpoint has been created, with the detailed verification report attached as a git note.

## Quality Gates

Before marking any task complete, verify:

### General Quality Gates
- [ ] All tests pass
- [ ] Code coverage meets requirements (>80%)
- [ ] Code follows project's code style guidelines (as defined in `code_styleguides/`)
- [ ] All public functions/methods are documented (e.g., docstrings, JSDoc, GoDoc)
- [ ] Type safety is enforced (e.g., type hints, TypeScript types, Go types)
- [ ] No linting or static analysis errors (using the project's configured tools)
- [ ] Works correctly on mobile (if applicable)
- [ ] Documentation updated if needed
- [ ] No security vulnerabilities introduced

### Project-Specific Quality Gates

#### TypeScript/React Quality Gates
- [ ] File headers present on all new files (required for `.ts`, `.tsx`, `.js`, `.jsx`)
- [ ] No `any` types in TypeScript (Google TypeScript Style Guide enforced)
- [ ] Named exports only (no default exports)
- [ ] Path alias `@/*` used consistently instead of relative imports
- [ ] Custom "Cyber Yellow" theme (`#FFD400`) applied correctly

#### Python Quality Gates
- [ ] File headers present on all new files (required for `.py`, `.pyi`)
- [ ] 4-space indentation, 80-character line limits (Google Python Style Guide)
- [ ] Router pattern used: `router = APIRouter(prefix="/path", tags=["Tag"])`
- [ ] Dependency injection via `Depends()` in FastAPI
- [ ] Use `127.0.0.1` not `localhost` in code (IPv6 compatibility)
- [ ] No global Python or pip usage - always use root venv (`../.venv/Scripts/python`)

## Development Commands

### Setup

```bash
# AURA-CHAT Frontend
 cd AURA-CHAT/client && npm install

# AURA-NOTES-MANAGER Frontend
cd AURA-NOTES-MANAGER/frontend && npm install

# Python Dependencies (use ROOT venv, never global)
../.venv/Scripts/pip install -r requirements.txt
```

### Daily Development

```bash
# AURA-CHAT Frontend (React 19 + Vite) - Port 5173
cd AURA-CHAT/client && npm run dev

# AURA-CHAT Backend (FastAPI) - Port 8000
cd AURA-CHAT/server && python main.py

# AURA-NOTES-MANAGER Frontend (React 18 + Vite) - Port 5173
cd AURA-NOTES-MANAGER/frontend && npm run dev

# AURA-NOTES-MANAGER Backend (FastAPI) - Port 8001
cd AURA-NOTES-MANAGER/api && python main.py
```

### Testing

```bash
# AURA-CHAT E2E Tests (parallel execution allowed)
cd AURA-CHAT/client && npm run test:e2e

# AURA-NOTES-MANAGER E2E Tests (sequential - DB consistency)
cd AURA-NOTES-MANAGER && npm run test:e2e

# Python Tests (always use root venv)
../.venv/Scripts/python -m pytest
```

### Before Committing

```bash
# ESLint check
npm run lint

# TypeScript type check (no emit)
npx tsc --noEmit

# Python linting (use root venv)
../.venv/Scripts/python -m pylint <module_name>

# Or run from within project directory
../.venv/Scripts/python -m pylint src/
```

## Testing Requirements

### Unit Testing
- Every module must have corresponding tests.
- Use appropriate test setup/teardown mechanisms (e.g., fixtures, beforeEach/afterEach).
- Mock external dependencies.
- Test both success and failure cases.

### Integration Testing
- Test complete user flows
- Verify database transactions
- Test authentication and authorization
- Check form submissions

### E2E Testing Specifics

**AURA-CHAT E2E:**
- Parallel execution allowed (`fullyParallel: true`)
- Uses modern React 19 + TanStack Query patterns
- Tests knowledge graph functionality

**AURA-NOTES-MANAGER E2E:**
- Sequential execution required (`fullyParallel: false`) for DB consistency
- Playwright tests in `e2e/` directory
- Tests staff hierarchy and note management flows

### Mobile Testing
- Test on actual iPhone when possible (Safari browser required)
- Use Safari developer tools
- Test touch interactions
- Verify responsive layouts
- Check performance on 3G/4G
- **Critical:** Both AURA-CHAT and AURA-NOTES-MANAGER must work on iPhone Safari

### Python Environment
- **ALWAYS use the root venv** (`../.venv/Scripts/python`) for all Python tasks
- **NEVER install dependencies globally** or in subdirectory venvs
- Correct: `../.venv/Scripts/python -m pytest tests/`
- Wrong: `python -m pytest tests/` or `pip install <package>`

## Nested Git Repos Warning

**⚠️ CRITICAL WARNING ⚠️**

This repository contains **nested Git repositories**:

- `AURA-CHAT/` has its own `.git/` directory
- `AURA-NOTES-MANAGER/` has its own `.git/` directory

### Important Guidelines:
- **Never perform cross-repo git operations** (e.g., running `git add` from root that affects both sub-repos)
- **Always run git commands from within each subdirectory** (`AURA-CHAT/` or `AURA-NOTES-MANAGER/`)
- Each sub-project is managed independently
- Plan files should reference which sub-project is being modified
- Be extra careful with git status/add/commit to ensure you're in the correct directory

### Project Structure Reminder:
```
AURA-PROJ/
├── .git/                    # Root repo
├── AURA-CHAT/
│   └── .git/                # Separate repo!
├── AURA-NOTES-MANAGER/
│   └── .git/                # Separate repo!
└── ...
```

## Code Review Process

### Self-Review Checklist
Before requesting review:

1. **Functionality**
   - Feature works as specified
   - Edge cases handled
   - Error messages are user-friendly

2. **Code Quality**
   - Follows style guide
   - DRY principle applied
   - Clear variable/function names
   - Appropriate comments

3. **Testing**
   - Unit tests comprehensive
   - Integration tests pass
   - Coverage adequate (>80%)

4. **Security**
   - No hardcoded secrets
   - Input validation present
   - SQL injection prevented
   - XSS protection in place

5. **Performance**
   - Database queries optimized
   - Images optimized
   - Caching implemented where needed

6. **Mobile Experience**
   - Touch targets adequate (44x44px)
   - Text readable without zooming
   - Performance acceptable on mobile
   - Interactions feel native

## Commit Guidelines

### Message Format
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests
- `chore`: Maintenance tasks

### Examples
```bash
git commit -m "feat(auth): Add remember me functionality"
git commit -m "fix(posts): Correct excerpt generation for short posts"
git commit -m "test(comments): Add tests for emoji reaction limits"
git commit -m "style(mobile): Improve button touch targets"
```

## Dual Project Considerations

When working on AURA Twin, remember these key differences:

### Port Configuration
- **AURA-CHAT Backend:** Port 8000
- **AURA-NOTES-MANAGER Backend:** Port 8001
- Both frontends use Port 5173 (run separately)

### Technology Differences
| Aspect | AURA-CHAT | AURA-NOTES-MANAGER |
|--------|-----------|-------------------|
| React Version | 19 (latest) | 18 |
| State Management | TanStack Query | Zustand + TanStack Query |
| Backend | `server/` (modern FastAPI) | `api/` (FastAPI) |
| Database | Neo4j (knowledge graph) + optional | Firestore (NoSQL) |
| AI Provider | Vertex AI | Gemini + Deepgram |
| E2E | Parallel | Sequential (DB consistency) |

### Shared Resources
- **Neo4j database** for knowledge graph (shared between both apps)
- **Google AI stack** (both use Google's AI services)
- **Root Python venv** (`../.venv/`)
- Path alias `@/*` convention

### Development Workflow
- Each project has independent dev servers
- Test commands differ between projects
- ESLint configs are project-specific
- Be aware of which project you're modifying when reading/writing files

## AI Agent Workflow Notes

### Research-First Principle
- **ALWAYS web-search before implementing** unfamiliar libraries, APIs, or patterns
- **NEVER assume** library behavior - verify with official documentation
- **Search first** when encountering: new npm packages, Python libraries, framework features, or external APIs
- Use `librarian` agent for documentation lookup, `explore` agent for codebase patterns

### Code Modification Protocol
- **Always read existing code before modifying** - understand context first
- **Run diagnostics before completing tasks** - verify no new errors introduced
- **Use sub-agents for complex tasks**:
  - `frontend-ui-ux-engineer` for visual/UI changes
  - `explore` for finding existing implementations
  - `librarian` for external documentation
  - `oracle` for architecture decisions or debugging after 2+ failed attempts

### File Header Requirements
**MANDATORY for every code file created or updated:**

```typescript
// {FILE_NAME}
// {Brief 1-line description of what this file does}

// Longer description (2-4 lines):
// - What problem does this solve?
// - What are the key functions/classes?
// - Any important context for future maintainers

// @see: {Related files}
// @note: {Important caveats or gotchas}
```

**Enforcement:**
- File headers are REQUIRED for: `.ts`, `.tsx`, `.py`, `.pyi`, `.js`, `.jsx`
- Existing files without headers: Add when modifying significantly (>30% changes)
- New files: ALWAYS add header before first write

### Verification Requirements
Task is NOT complete without:
- [ ] `lsp_diagnostics` clean on changed files
- [ ] Build passes (if applicable)
- [ ] Tests pass (or explicit note of pre-existing failures)
- [ ] User's original request fully addressed
- [ ] File headers present
- [ ] No new TypeScript errors
- [ ] No new linting errors

### Best Practices
- **Write tests BEFORE or WITH code**, not after
- **Minimal changes:** Fix bugs without refactoring unrelated code
- **Never suppress type errors** with `as any`, `@ts-ignore`
- **Never leave empty catch blocks** `catch(e) {}`
- **Never be lazy:** Don't skip verification, don't guess, don't assume knowledge
- **Certainty before conclusion:** Never declare complete without 100% confidence

## Definition of Done

A task is complete when:

1. All code implemented to specification
2. Unit tests written and passing
3. Code coverage meets project requirements
4. Documentation complete (if applicable)
5. Code passes all configured linting and static analysis checks
6. Works beautifully on mobile (if applicable)
7. Implementation notes added to `plan.md`
8. Changes committed with proper message
9. Git note with task summary attached to the commit
10. File headers present on all new/modified files
11. No type errors or linting violations
12. Diagnostics run and clean

## Emergency Procedures

### Critical Bug in Production
1. Create hotfix branch from main
2. Write failing test for bug
3. Implement minimal fix
4. Test thoroughly including mobile
5. Deploy immediately
6. Document in plan.md

### Data Loss
1. Stop all write operations
2. Restore from latest backup
3. Verify data integrity
4. Document incident
5. Update backup procedures

### Security Breach
1. Rotate all secrets immediately
2. Review access logs
3. Patch vulnerability
4. Notify affected users (if any)
5. Document and update security procedures

## Deployment Workflow

### Pre-Deployment Checklist
- [ ] All tests passing
- [ ] Coverage >80%
- [ ] No linting errors
- [ ] Mobile testing complete
- [ ] Environment variables configured
- [ ] Database migrations ready
- [ ] Backup created

### Deployment Steps
1. Merge feature branch to main
2. Tag release with version
3. Push to deployment service
4. Run database migrations
5. Verify deployment
6. Test critical paths
7. Monitor for errors

### Post-Deployment
1. Monitor analytics
2. Check error logs
3. Gather user feedback
4. Plan next iteration

## Continuous Improvement

- Review workflow weekly
- Update based on pain points
- Document lessons learned
- Optimize for user happiness
- Keep things simple and maintainable
