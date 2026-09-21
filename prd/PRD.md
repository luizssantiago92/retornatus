# Retornatus — Product Requirements Document

**Document:** `PRD.md`  
**Product:** Retornatus  
**Version:** V1  
**Status:** Architecture Stable / Ready for Implementation  
**Distribution:** Python / PyPI  
**Primary execution:** `uvx`  
**Persistent installation:** `uv tool install`

---

# 1. Product Definition

Retornatus is a repo-native governance harness for AI-assisted software development.

It transforms engineering intent into structured, governed, evidence-backed work across AI coding environments while preserving the native capabilities of those environments.

Retornatus does not attempt to replace coding agents, execution environments, sandboxes, worktrees, subagents, or other capabilities already provided effectively by the host environment.

Instead, Retornatus governs engineering work and constrains the agents performing that work through explicit contracts, rules, authority, boundaries, evidence, assurance, memory, and adaptation.

Its core operating principle is:

> **Govern the work. Bound the agent. Verify the outcome.**

Retornatus represents return with accumulated evidence, memory, and learning: each new iteration should be informed by what came before rather than blindly repeating previous work.

---

# 2. Product Philosophy

Retornatus is built around several foundational principles.

## 2.1 Governance over orchestration theater

The Harness exists to provide:

- governance;
- coordination;
- continuity;
- assurance.

The execution environment provides capabilities.

```text
Agent Environment
        ↓
    CAPABILITY

Retornatus
        ↓
    GOVERNANCE
    COORDINATION
    CONTINUITY
    ASSURANCE
```

## 2.2 Native first

Retornatus must prefer native environment capabilities whenever they sufficiently preserve the required guarantees.

> **Native first.**

> **Govern, don't duplicate.**

> **Preserve native advantage.**

> **Implement only the missing capability.**

> **Do not rebuild isolation that the execution environment already provides.**

> **Spend complexity on governance, not on rebuilding the host.**

## 2.3 Complexity must be earned

Before introducing a new mechanism:

1. determine whether Retornatus already has a sufficient mechanism;
2. determine whether the execution environment already provides the capability;
3. investigate established external patterns when useful;
4. implement a new mechanism only when the problem remains unsolved.

> **A mechanism must save more complexity than it introduces.**

> **Start with the lightest mechanism that preserves the required guarantee.**

> **Complexity must be earned by a concrete failure mode.**

## 2.4 Agents are executors, not architectural centers

Retornatus governs work first.

Agents perform bounded executions within that governed system.

Rules, Policy, Authority, Boundaries, Context, Allocation, and Assurance may directly constrain agent behavior.

However, permanent Agent identities, Agent hierarchies, Agent Pools, Reviewer Agents, and similar abstractions are not part of the V1 domain model.

Specialization should emerge from:

```text
Assignment
+
Context
+
Skills
+
Capabilities
+
Environment
```

not from permanent Agent personas.

---

# 3. Product Scope

Retornatus V1 is specifically designed for software engineering.

It is not intended to be a universal work orchestration platform.

Target environments include:

- Cursor;
- Claude Code;
- Codex;
- cloud coding agents;
- future compatible AI coding environments.

Retornatus must remain environment-aware without becoming environment-dependent.

Projects depend on capabilities, not specific environments.

---

# 4. Distribution

Retornatus V1 is a Python-only Core distributed through PyPI.

Primary usage:

```bash
uvx retornatus
```

Persistent installation:

```bash
uv tool install retornatus
```

Retornatus may govern projects implemented in any programming language.

Python is the implementation language of the Harness, not a restriction on governed projects.

> **Distribution is not architecture.**

---

# 5. Repository-Native Architecture

Retornatus V1 requires no:

- control plane;
- remote database;
- SaaS runtime;
- Retornatus server;
- mandatory cloud account.

Persistent Retornatus state lives inside the governed repository.

A single hidden directory owns Retornatus-specific state:

```text
project/
├── src/
├── tests/
├── docs/
└── .retornatus/
```

Environment-specific bridge files may exist outside `.retornatus/` only when required by the execution environment.

---

# 6. Canonical Storage Model

Retornatus uses different storage formats according to the nature of the information.

```text
Human Semantic Content
        ↓
     Markdown

Structured Domain Data
        ↓
       JSON

Configuration
        ↓
       TOML

Derived Search / Relations
        ↓
 SQLite + FTS5
```

V1 canonical formats:

- Markdown;
- JSON;
- TOML.

Derived infrastructure:

- SQLite;
- SQLite FTS5.

Explicitly excluded from V1 unless a concrete failure mode proves necessary:

- YAML;
- JSONL event stores;
- graph databases;
- vector databases;
- remote databases;
- runtime databases.

> **Files persist truth. Models validate truth. SQLite indexes and finds truth.**

---

# 7. Ownership of Structure

Agents and humans express intent.

Retornatus owns structural integrity.

```text
Agent / Human
      ↓
expresses intent
      ↓
Retornatus Operation
      ↓
Domain Model Validation
      ↓
Safe Persistence
      ↓
Assurance
```

Agents should not be expected to maintain Retornatus invariants through manual file editing when a structured Retornatus operation exists.

> **Humans and Agents express intent. The Harness owns structure.**

---

# 8. Domain Architecture

The conceptual architecture is:

```text
RETORNATUS
│
├── PROJECT CONTINUITY
│   └── Memory
│
├── GOVERNANCE
│   ├── Rule
│   ├── Policy
│   ├── Authority
│   └── Boundaries
│
├── ENVIRONMENT
│   ├── Wake Up
│   ├── Capability Model
│   └── Adapter
│
├── CHANGE
│   ├── Demand
│   ├── Situation
│   ├── Contract
│   ├── Action
│   │   └── Task
│   ├── Execution
│   ├── Finding
│   ├── Question
│   ├── Evidence
│   ├── Assurance
│   └── Resolution
│
└── ADAPTATION
    ├── Learning
    ├── Skill
    └── Graduation
          ↓
       Rule Candidate
```

Auxiliary capabilities/processes:

- Task Graph;
- Synchronization;
- Allocation;
- Context Assembly;
- Retrieval.

Recognized architectural patterns:

- Convergence;
- Divergence;
- Iteration.

These patterns must not automatically become engines, managers, or persistent entities.

> **Pattern before mechanism. Mechanism only if repeated implementation proves necessary.**

---

# 9. Change

A Change is the bounded engineering context through which a coherent project change is understood, authorized, executed, and assured.

A Change may represent:

- new capability;
- bug fix;
- refactor;
- migration;
- maintenance;
- security correction;
- dependency change;
- behavior change.

Conceptually:

```text
PROJECT
│
└── CHANGE
     ├── Demand
     ├── Situation
     ├── Contract
     ├── Action
     │   └── Task
     ├── Finding
     ├── Question
     ├── Evidence
     └── Assurance
```

Change is primarily a bounded engineering context.

It must not become an unnecessary mega-entity containing every implementation detail.

---

# 10. Demand

A Demand is an expressed need for the project to change or achieve something.

Examples:

- implement a capability;
- correct a bug;
- refactor a subsystem;
- perform a migration;
- change behavior;
- perform maintenance;
- address an explicitly reported security problem.

Demand describes the need.

It does not describe implementation.

---

# 11. Situation

Situation is the structured understanding of the current reality surrounding a Demand.

It may include:

- relevant repository state;
- existing architecture;
- constraints;
- dependencies;
- known risks;
- affected surfaces;
- relevant historical context;
- unresolved ambiguity.

Situation exists to make the Demand sufficiently understood before obligations are formalized.

---

# 12. Contract

Contract is the authoritative agreement that transforms an understood Demand into explicit obligations, boundaries, and satisfaction conditions.

Conceptually:

```text
Contract
=
WHAT
+
Constraints
+
DONE
```

Contract does not prescribe unnecessary implementation detail.

Action represents the response to the Contract.

Once active, a Contract is immutable.

A material change requires:

1. reopening Situation;
2. producing a new Contract version.

An approved Contract implicitly authorizes its legitimate implementation unless Authority, Rules, or Boundaries require further human judgment.

---

# 13. Action

Action is the structured response undertaken to satisfy a Contract or resolve a Question.

An Action originates from either:

```text
Contract
or
Question
```

Conceptual structure:

```text
Action
├── ID
├── Origin
├── Objective
├── Scope
├── Constraints
├── Success Conditions
├── Authority
└── Tasks? [conditional]
```

Action must not durably store information that can be reliably derived, including:

- current Agent;
- current Environment;
- Workspace implementation details;
- loaded Skills;
- parallelism decisions.

> **Action defines work; Allocation assigns capacity; Execution performs it.**

> **An Action must know what success means before execution begins.**

> **Do not store what can be reliably derived.**

---

# 14. Task

Task is a bounded and verifiable unit of work derived from an Action.

Tasks are conditional.

Simple Actions should not be decomposed merely because Retornatus supports Tasks.

Candidate minimal lifecycle:

```text
PENDING
↓
ACTIVE
↓
COMPLETED
```

Failure may result in:

```text
FAILED
```

Task is an obligation.

Task is not an Execution.

In V1, Tasks should initially be embedded inside the Action artifact unless a demonstrated failure mode requires independent persistence.

---

# 15. Task Graph

Task Graph is the derived dependency structure connecting Tasks within an Action.

Dependencies should be represented through relations such as:

```text
depends_on
```

The graph is derived.

No independent `task-graph.json` is required.

> **Dependencies determine readiness; they do not prescribe executor.**

---

# 16. Synchronization

Synchronization coordinates readiness and progression of concurrent work within an Action.

It must prevent conflicting concurrent writers.

Core principles:

> **No concurrent conflicting writers.**

> **Dependencies determine readiness; they do not prescribe executor.**

> **Resource conflicts constrain concurrency without fake dependencies.**

> **Readiness is derived state, not durable truth.**

> **Waves are projections, not mandatory barriers.**

> **Synchronization coordinates work; Allocation allocates resources.**

---

# 17. Wave

Wave is a useful runtime projection of currently compatible work.

Wave is not:

- a domain entity;
- a durable lifecycle;
- a database object;
- a mandatory execution barrier.

Retornatus may display or derive waves when useful.

It must not force work into artificial wave boundaries.

---

# 18. Allocation

Allocation matches ready work with execution capabilities and resources available in the current environment.

V1 Allocation concerns:

- Executor Selection;
- Workspace Selection;
- Concurrency Allocation.

```text
Ready Work
+
Execution Requirements
+
Environment Capabilities
+
Available Resources
↓
Allocation
```

> **Allocation expresses execution requirements; Environment realizes them.**

Retornatus must not implement in V1:

- Agent Pool;
- Workspace Pool;
- persisted executor slots;
- distributed schedulers;
- Kubernetes-like orchestration.

Multi-agent execution is an Allocation outcome, not an architectural mechanism.

Default behavior:

```text
single Agent
+
single Workspace
+
sequential execution
```

Parallelism is enabled only when useful and safe.

> **Parallelizable does not mean should be parallelized.**

> **Available concurrency is a capability, not a target.**

---

# 19. Execution

Execution is a bounded occurrence of performing assigned engineering work within a specific environment, context, and authority.

Task describes what must be accomplished.

Execution describes an occurrence or attempt to accomplish work.

Execution may cover:

- implementation;
- testing;
- review;
- security analysis;
- investigation;
- debugging;
- refactoring;
- migration;
- research;
- correction;
- validation.

Conceptually:

```text
Execution
=
Assignment
+
Context
+
Skills
+
Capabilities
+
Environment
+
Authority / Boundaries
```

Execution may produce:

- Outcome;
- Artifacts;
- Evidence;
- Findings;
- observations.

> **An Execution operates against a stable Assignment, Context, and Skill snapshot.**

> **Retry is one possible response to failure, not the failure model.**

> **Specialization comes from Assignment, Context, and Skills — not permanent Agent identity.**

---

# 20. Finding

Finding records what was discovered.

A Finding is a relevant observation.

It is not automatically:

- work;
- a Task;
- a Question;
- a Rule;
- a failure.

Findings may originate from:

- Execution;
- Assurance;
- Review;
- Security analysis;
- Testing;
- Research;
- Environment;
- Human observation.

Findings are Change-owned by default.

A Finding becomes the basis for a Question only when an independent response is required.

---

# 21. Question

Question is the structured problem grounded in one or more Findings that requires an independent response.

> **A Question must be grounded in at least one Finding.**

Normal path:

```text
Observation
↓
Finding
↓
independent response required?
↓
Question
```

A direct external request such as:

```text
"Fix the authentication bypass."
```

is a Demand.

A security condition discovered during execution becomes:

```text
Finding
↓
Question
```

Candidate minimal lifecycle:

```text
OPEN
↓
RESOLVED
```

Duplicate, superseded, and not-actionable conditions should be represented as dispositions rather than expanding the lifecycle unnecessarily.

> **Resolved means the Question received a sufficient response, not merely that work stopped.**

Multiple Findings may ground one Question.

One Finding may ground multiple Questions when genuinely necessary.

---

# 22. Resolution

Resolution is the satisfactory closure or outcome of a Question.

V1 should treat Resolution primarily as an embedded closure record or Outcome rather than creating an independent persistent entity unless identity requirements emerge.

A typical flow:

```text
Finding
↓
Question
↓
Action
↓
Execution
↓
Evidence
↓
Assurance
↓
Resolution
```

The executing Agent cannot independently declare a Question resolved.

> **Resolution is established, not claimed.**

If the same condition reappears within the same Change, the existing Question may be reopened or reinforced.

If it appears in a later Change, create a new local Question and connect historical context through Memory and Learning.

> **Questions resolve locally; Memory connects historically.**

---

# 23. Evidence

Evidence is attributable observable information that supports or challenges a claim about an engineering outcome.

Examples:

- test result;
- static analysis result;
- benchmark;
- build result;
- diff inspection;
- runtime observation;
- security scan;
- human decision;
- externally attributable technical observation.

Minimal structure:

```text
Evidence
├── ID
├── Type
├── Subject / Claim
├── Source
├── Producer
├── Observed At
└── Subject State
```

Evidence validity and staleness should be derived from the current state of its subject whenever possible.

> **Evidence validity should be derived whenever possible, not manually maintained.**

> **LOG ≠ EVIDENCE**

> **Agent conclusion ≠ Evidence**

Evidence may be produced by an Execution or imported from an attributable source.

---

# 24. Assurance

Assurance determines and evaluates the evidence required to establish sufficient confidence that an engineering outcome satisfies its Contract and applicable quality expectations.

Operational model:

```text
ASSURANCE
├── Determine Claims
├── Determine Required Evidence
├── Acquire Evidence
├── Evaluate
└── Verdict
```

V1 verdicts:

```text
SATISFIED
NOT_SATISFIED
INCONCLUSIVE
```

`INCONCLUSIVE` is used when required capability or evidence is unavailable.

Principles:

> **Assurance must be proportional to claims, risk, and affected surfaces.**

> **Independent Assurance must not inherit the author's conclusions.**

> **Use deterministic checks before probabilistic judgment whenever sufficient.**

> **Deterministic success is evidence, not final judgment.**

> **A green test suite is evidence, not proof of overall correctness.**

> **Independent Assurance observes and judges; corrective writing occurs in separate Execution.**

> **Assurance aggregates evidence, not Agent votes.**

Assurance ends when:

1. required claims have sufficient evidence;
2. no blocking unresolved Questions remain.

Code review is an Assurance Execution.

It is not an independent subsystem.

---

# 25. Convergence and Divergence

Convergence and Divergence are architectural patterns.

They are not V1 engines.

Convergence reduces multiplicity into coherent meaning.

Examples:

```text
Findings
↓
Question
```

```text
Evidence
↓
Assurance
```

```text
Experiences
↓
Learning
```

Divergence turns coherent meaning into context-appropriate responses.

Examples:

```text
Question
↓
Action / Human Decision / new Demand
```

```text
Action
↓
Direct Execution / Tasks
```

```text
Assurance
↓
SATISFIED / NOT_SATISFIED / INCONCLUSIVE
```

```text
Adaptation
↓
Learning / Skill Evolution / Graduation
```

Retornatus V1 must not introduce:

- `ConvergenceEngine`;
- `DivergenceEngine`.

> **Recognize the pattern before implementing the abstraction.**

---

# 26. Iterative Convergence

Retornatus uses iterative convergence as an emergent workflow property.

Operationally:

```text
Intent
  ↓
CONVERGE
  ↓
Contract
  ↓
DIVERGE
  ↓
Action / Tasks / Executions
  ↓
OBSERVE
  ↓
Findings + Evidence
  ↓
CONVERGE
  ↓
Question / Assurance
  ↓
        ┌── gap ──→ DIVERGE ──→ Action
        │
        └── sufficient ──→ Resolution
                              ↓
                          Adaptation
```

Iteration means:

```text
ACT
↓
OBSERVE
↓
EVALUATE
↓
ACT AGAIN
```

A new iteration should be driven by changed information such as:

- new Evidence;
- new Finding;
- new Question;
- failed claim;
- Environment change;
- Human decision.

> **Iteration without new information is repetition.**

Retornatus should not implement a dedicated Loop Engine in V1.

---

# 27. Environment

Environment represents the execution context in which Retornatus currently operates, including native capabilities, constraints, configuration, and integration surfaces.

Environment is a stable subsystem containing:

```text
ENVIRONMENT
├── Wake Up
├── Capability Model
└── Environment Adapter
```

---

# 28. Wake Up

Wake Up is the environment-aware adaptive initialization process through which Retornatus:

1. understands the project;
2. discovers the current execution environment;
3. identifies relevant native capabilities;
4. identifies constraints;
5. restores project continuity;
6. prepares itself to exploit the environment without unnecessarily reproducing it.

> **Wake Up identifies both capability gaps and capability opportunities.**

> **Discover broadly enough to orient; probe deeply when work requires it.**

Candidate Wake Up flow:

```text
Locate Project
↓
Read config.toml
↓
Validate canonical artifacts
↓
Check schema compatibility
↓
Run required migrations
↓
Detect Environment
↓
Load Adapter
↓
Discover capabilities
↓
Validate / rebuild index
↓
Find relevant Change
↓
Derive status
↓
Resolve applicable Rules
↓
Retrieve relevant Memory
↓
READY
```

---

# 29. Capability Model

Retornatus should reason about capabilities rather than hard-code behavior around named environments.

Candidate capabilities include:

```text
EXECUTION_CONTROL
SUBAGENTS
ISOLATED_WORKSPACE
RULE_REALIZATION
SHELL
STRUCTURED_OUTPUT
FILE_OPERATIONS
```

Projects depend on capabilities, not environments.

Fallback strategy:

```text
native equivalent
↓
native composition
↓
Retornatus portable capability
↓
external integration
↓
minimal portable fallback
↓
Environment change / Human decision
```

> **A missing native capability does not automatically become a Retornatus feature.**

> **Portability should preserve required guarantees, not reproduce environment-specific implementations.**

---

# 30. Environment Adapter

Environment Adapters translate Retornatus semantic requirements into environment-specific realization.

Candidate semantic API:

```text
identify()
discover_capabilities()
prepare_execution()
execute()
collect_result()
realize_rule()
release()
```

Exact signatures are implementation details.

`execute()` is not mandatory when the host environment owns execution.

> **Core speaks capabilities. Adapter speaks environment.**

Adapters must not contain domain policy that belongs in Core.

---

# 31. Governance

Governance consists of:

```text
GOVERNANCE
├── Rule
├── Policy
├── Authority
└── Boundaries
```

Governance applies to work and may directly constrain the Agents performing that work.

---

# 32. Authority

Authority defines which decisions require human judgment and which may be resolved autonomously by Retornatus and its Agents.

Candidate authority categories:

```text
RULED
DELEGATED
HUMAN
```

Creating or activating an authoritative Rule requires human validation.

Agents and Retornatus may propose Rule Candidates.

They may not unilaterally convert those candidates into authoritative Rules.

---

# 33. Boundaries

Boundaries represent:

1. effective technical limits of the current Environment;
2. limits imposed by Retornatus governance.

Examples:

- filesystem;
- network;
- tools;
- environment;
- execution scope.

Candidate realization states:

```text
ENFORCED
ADVISORY
UNAVAILABLE
```

Retornatus should use native sandboxing and permission mechanisms whenever sufficient.

Do not rebuild environment isolation without a concrete need.

---

# 34. Rule

Rule is an authoritative project constraint established from validated experience or explicit human intent, applicable to matching future work.

Rules may originate from:

1. explicit Human intent;
2. validated Graduation from project experience.

Adaptation path:

```text
Experience
↓
Learning
↓
persistent / consequential problem
↓
Graduation
↓
Rule Candidate
↓
Human Validation
══════════════════ AUTHORITY BOUNDARY
Active Rule
↓
future matching work
```

A Rule may influence:

```text
                    RULE
                      │
                applicability
                      ↓
                matching work
                      │
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
     Context       Assurance    Enforcement
                                  /        \
                            Retornatus    Environment
                                           native
```

> **Rule defines the constraint. Environment may provide its strongest realization.**

> **Rule is semantic truth; enforcement is a projection of that truth.**

> **Rule semantics are stable; enforcement is capability-dependent.**

Possible application modes:

- Instructional;
- Assurable;
- Enforceable.

These are not separate Rule types unless implementation evidence later requires that distinction.

---

# 35. Policy

Policy evaluates governed effects and transitions against applicable Rules, Authority, and Boundaries.

```text
proposed governed effect
+
applicable Rules
+
Authority
+
Boundaries
↓
Policy
↓
ALLOW | DENY | REQUIRE_HUMAN
```

Not every Rule requires a Policy decision.

Rules may also act through:

- Context;
- Assurance;
- native Environment enforcement.

---

# 36. Memory

Memory is the durable, attributable, and relational continuity of the project's engineering history and learned knowledge.

```text
Memory
=
durable engineering continuity
```

Memory is not Runtime.

Memory is not Status.

Memory is not Evidence.

Memory is not Skill.

> **Memory remembers; it does not decide.**

> **Memory preserves continuity; Runtime preserves operation.**

> **Repository owns code truth; Memory owns engineering continuity.**

Responsibilities:

- Preserve;
- Relate;
- Trace;
- Supersede;
- Recall.

Memory must support:

- selective persistence;
- provenance;
- validity;
- conflicts;
- ownership;
- applicability;
- explicit relations;
- relevance-based retrieval.

No graph database is required.

No vector database is required in V1.

---

# 37. Learning

Learning preserves relevant project experience so future Agents do not approach a known situation as if it had never happened before.

> **Learning records experience.**

A Learning should answer:

> Could preserving what was just learned materially help another Agent facing a similar situation?

Learning is retrieved by relevance.

It must not be loaded globally by default.

Difference:

```text
Learning
"What happened before?"

Skill
"How should this kind of work be performed?"

Rule
"What must or must not happen?"
```

> **Learning informs; Rules constrain.**

> **Rule is escalation, not Adaptation's default output.**

> **A persistent error may trigger Graduation, but recurrence never creates a Rule automatically.**

---

# 38. Learning Persistence

Learning uses Markdown as canonical storage.

Example:

```text
.retornatus/
└── adaptation/
    └── learnings/
        ├── L-0001.md
        ├── L-0002.md
        └── ...
```

Search metadata and relationships may be projected into:

```text
.retornatus/index/retornatus.db
```

> **Learning lives in files. SQLite helps Retornatus find it.**

> **Durable truth must not exist only inside SQLite.**

Deleting the index must never delete Learning.

---

# 39. Skill

Skill is reusable procedural knowledge for performing a class of engineering work.

Skills may be:

- Environment-native;
- Retornatus-provided;
- Project-specific.

If an Environment-native Skill mechanism is sufficient, Retornatus should use it.

Retornatus should not create a proprietary Skill DSL merely for architectural symmetry.

Executions consume stable Skill snapshots.

Agents consume Skills.

Agents do not own Skills.

An Execution should not directly rewrite a Skill while consuming it.

Skill evolution belongs to Adaptation.

---

# 40. Adaptation

Adaptation changes future Retornatus behavior based on validated project experience.

```text
ADAPTATION
├── Learning
├── Skill Evolution
└── Graduation
```

Inputs may include:

- Resolution;
- Evidence;
- Assurance;
- Execution experience.

Outputs may include:

- Learning;
- Skill improvement;
- Rule Candidate.

Adaptation does not own active Rules after the Authority boundary.

---

# 41. Graduation

Graduation is the process through which project experience may justify proposing an authoritative Rule.

```text
Resolution(s)
     ↓
Learning
     ↓
persistent problem /
Learning or Skill insufficient?
     ↓
Graduation
     ↓
Rule Candidate
     ↓
Human Decision
   /          \
 reject       approve
                ↓
              Rule
```

Graduation is a Process inside Adaptation.

It is not an independent Entity.

> **Recurrence may trigger consideration; recurrence never creates authority.**

> **Recurrence is evidence for Graduation, not a prerequisite for it.**

A single severe issue may justify a Rule Candidate.

No automatic Graduation to authoritative Rule is allowed.

---

# 42. Context Assembly

Execution contexts are assembled rather than inherited.

Inputs may include:

```text
Assignment
+
Contract subset
+
Action / Task
+
Applicable Rules
+
Relevant Learning
+
Required Skills
+
Relevant Decisions
+
Relevant code references
+
Environment capabilities
+
Authority
+
Boundaries
```

Output:

```text
ExecutionContext
```

ExecutionContext should be an ephemeral validated model.

No mandatory `context.md` per Execution is required.

> **Execution contexts are assembled, not inherited.**

> **Context follows responsibility.**

> **Pass references when the receiver can retrieve the source; pass content only when needed now.**

> **Context should be sufficient, not comprehensive.**

---

# 43. Runtime

Runtime represents what is happening now.

Examples:

- active Execution;
- locks;
- workspace leases;
- context packages;
- Environment process information;
- temporary capability cache.

Runtime must contain only information that is truly ephemeral or not safely derivable during active operation.

Runtime is disposable.

```text
.retornatus/runtime/
├── locks/
├── executions/
└── cache/
```

> **Runtime is disposable.**

Deleting Runtime must not destroy semantic project history.

---

# 44. Status

Status is a human-readable projection derived from durable and runtime state.

```text
DURABLE
Contract
Action
Task
Question
...

↓ derive

RUNTIME
active Execution
ready Tasks
workspace Allocation
current Environment

↓ derive

STATUS
human-readable projection
```

> **Status is a projection, not truth.**

No canonical `state.json` should exist merely to duplicate information already derivable from canonical artifacts.

---

# 45. Restart Guarantee

Retornatus must survive interruption.

After a restart:

```text
Retornatus restart
↓
Wake Up
↓
read durable state
↓
inspect repository
↓
inspect Environment
↓
validate / rebuild index
↓
reconstruct Runtime
↓
continue safely
```

A process crash must not require reconstructing project intent from conversation history.

---

# 46. Failure and Recovery

Retornatus does not require a Recovery subsystem.

Failure routes through existing semantics.

Expected local failure:

```text
test RED
↓
continue current Execution
```

Significant unexpected or persistent issue:

```text
Observation
↓
Finding
↓
Question
↓
Action
```

Issue invalidating original intent:

```text
Question
↓
new Demand / Contract reconsideration
```

> **Recovery is routing through existing semantics, not a separate architecture.**

---

# 47. Review

Code Review is not an independent subsystem.

Review is modeled as an Assurance Execution:

```text
Assurance
↓
review required
↓
Execution(
  assignment = review,
  fresh context
)
↓
Evidence
↓
Assurance
```

> **Review must evaluate the artifact, not inherit the author's belief.**

No permanent Reviewer Agent is required.

---

# 48. Human Decision Model

Retornatus should minimize approval fatigue.

Human escalation should follow:

1. explain the decision context;
2. present up to three viable alternatives;
3. optionally identify a recommended alternative;
4. provide `Other`;
5. provide `Explain the problem`;
6. allow the Human to decide.

Principles:

> **Escalate decisions, not implementation details.**

> **Don't ask for permission when the answer is already known.**

> **Human approval is the exception, not the operating model.**

> **Approval propagates downward.**

> **Implementation freedom is inherited from approved intent, not granted operation by operation.**

> **A Human is required when new information materially changes an existing agreement, not merely because implementation details were previously unspecified.**

---

# 49. Boundary Analysis

Every mechanism must have a clear boundary of responsibility.

When evaluating a mechanism, distinguish:

## Ownership

Where does this concept belong?

## Applicability

Where does its meaning or Rule apply?

## Operational Boundary

What may it affect or operate on?

## Lifetime

How long does it remain valid or useful?

## Authority

What may it decide, constrain, or authorize?

Retrieval is separate:

```text
Who can discover it?
When should it be loaded?
```

Principles:

> **Ownership is not applicability.**

> **Local ownership does not imply temporary existence.**

> **Retrievability does not change ownership.**

> **Crossing a boundary requires an explicit relationship or transformation.**

> **Project-wide persistence does not imply project-wide authority.**

> **The narrowest sufficient boundary should win.**

> **A mechanism must know not only what it does, but where its responsibility ends.**

> **Change-local experience does not become Project truth automatically.**

---

# 50. Relationship Vocabulary

Retornatus should use a small canonical relation vocabulary.

Initial relations:

```text
DERIVED_FROM
GROUNDED_IN
PRODUCES
SATISFIES
SUPPORTS
CHALLENGES
RESOLVES
APPLIES_TO
SUPERSEDES
RELEVANT_TO
```

Relationships belong to canonical entity metadata.

SQLite may derive relational projections for search and traversal.

No `graph.json` is required.

No Graph Database is required.

---

# 51. Identifier Model

Project-level identifiers:

```text
L-0001   Learning
R-0001   Rule
D-0001   Decision
```

Change identifier:

```text
C-0001
```

Change-owned identifiers:

```text
C-0001/A-001
C-0001/T-001
C-0001/F-001
C-0001/Q-001
C-0001/E-001
```

V1 does not require UUIDs.

ID allocation must prevent collisions through a simple centralized or atomic allocation strategy.

Do not introduce distributed ID infrastructure.

---

# 52. Physical Filesystem

Candidate stable V1 structure:

```text
.retornatus/
│
├── config.toml
│
├── project/
│   ├── project.md
│   └── decisions/
│
├── changes/
│   └── C-0001/
│       ├── change.json
│       ├── situation.md
│       ├── contract.json
│       │
│       ├── actions/
│       │   └── A-001.json
│       │
│       ├── findings/
│       │   └── F-001.json
│       │
│       ├── questions/
│       │   └── Q-001.json
│       │
│       └── evidence/
│           └── E-001.json
│
├── governance/
│   └── rules/
│       └── R-0001.json
│
├── adaptation/
│   ├── learnings/
│   │   └── L-0001.md
│   └── skills/
│
├── index/
│   └── retornatus.db
│
└── runtime/
    ├── locks/
    ├── executions/
    └── cache/
```

This structure may evolve only when implementation evidence demonstrates a concrete need.

---

# 53. Structured Domain Models

Structured artifacts should be validated through Pydantic models.

Example flow:

```text
Markdown / JSON / TOML
        ↓
      Parsers
        ↓
   Pydantic Models
        ↓
    DOMAIN CORE
```

Pydantic should be used for:

- validation;
- serialization;
- schema generation;
- typed boundaries.

Storage formats are implementation details.

Domain semantics are the contract.

> **Storage format is an implementation detail; domain semantics are the contract.**

---

# 54. Schema Versioning

Every structured canonical artifact must contain:

```json
{
  "schema_version": 1
}
```

Retornatus must maintain an explicit migration registry.

Conceptually:

```text
v1
↓
migration
↓
v2
↓
migration
↓
v3
```

Migrations must be:

- deterministic;
- testable;
- safe;
- explicit;
- idempotent where practical.

Retornatus must not perform silent destructive migrations.

An incompatible schema must cause Retornatus to stop with a clear diagnostic rather than guessing.

---

# 55. Persistence Layer

No Application or Domain code should perform scattered direct filesystem writes.

Required direction:

```text
Domain / Application
        ↓
 Repository Interface
        ↓
 File Repository
        ↓
 Serializer
        ↓
 Atomic Write
```

This creates a single persistence boundary for:

- validation;
- serialization;
- optimistic concurrency;
- atomic writes;
- index invalidation;
- migrations.

---

# 56. Atomic Mutation

Canonical mutation should follow:

```text
validate
↓
serialize
↓
write temporary file in same directory
↓
flush
↓
atomic replace
↓
update / invalidate derived index
```

Python `os.replace()` should be preferred for same-filesystem atomic replacement where appropriate.

The canonical artifact must be successfully persisted before the derived index is treated as updated.

---

# 57. Optimistic Concurrency

Retornatus should protect against stale concurrent mutation.

Candidate strategy:

```text
read artifact
↓
record version / hash
↓
prepare mutation
↓
verify expected version / hash
↓
write
```

If the artifact changed:

```text
CONFLICT
↓
reload
↓
reconcile
```

Synchronization should prevent obvious conflicting writers.

Optimistic concurrency protects remaining races.

No distributed lock service is required.

---

# 58. SQLite Derived Index

SQLite is a derived search and relationship index.

Candidate responsibilities:

- entity discovery;
- relation traversal;
- FTS5 search;
- metadata lookup;
- relevance support.

Candidate logical tables:

```text
entities
relations
documents
metadata
FTS virtual tables
```

Canonical write occurs first.

Index update occurs afterward.

If a crash occurs between the two:

```text
canonical truth valid
+
index potentially stale
↓
Wake Up
↓
detect / rebuild
```

Critical invariant:

```text
DELETE .retornatus/index/retornatus.db
↓
retornatus wake
↓
rebuild
↓
system remains semantically intact
```

SQLite WAL mode is not required by default.

It may be introduced only if demonstrated concurrency needs justify it.

---

# 59. Retrieval

Retrieval must be relevance-based.

V1 should begin with:

- structured metadata;
- relationships;
- SQLite FTS5;
- explicit references.

Do not introduce embeddings or vector databases until retrieval quality demonstrates a concrete deficiency.

> **Use the lightest retrieval mechanism that preserves useful recall.**

---

# 60. Application Architecture

Logical direction:

```text
Agent / CLI / Adapter
        ↓
   Application API
        ↓
     Domain Core
        ↓
   Repository API
        ↓
 Markdown / JSON / TOML
        ↓
      Indexer
        ↓
 SQLite + FTS5
```

CLI, Agent integration, and Environment Adapter must not duplicate domain logic.

---

# 61. Python Package Structure

Target logical structure:

```text
src/retornatus/
├── cli/
│
├── domain/
│   ├── models/
│   ├── relations.py
│   └── services/
│
├── application/
│   ├── change/
│   ├── execution/
│   ├── assurance/
│   ├── governance/
│   └── adaptation/
│
├── infrastructure/
│   ├── persistence/
│   ├── index/
│   └── environment/
│
└── bootstrap/
    └── wake.py
```

This is a logical target, not a requirement to create empty directories.

Packages should emerge when implementation requires them.

Dependency direction:

```text
CLI
 ↓
APPLICATION
 ↓
DOMAIN

INFRASTRUCTURE
implements ports required above
```

Domain must not know about:

- Cursor;
- Claude Code;
- Codex;
- SQLite;
- filesystem implementation;
- CLI;
- uv.

---

# 62. CLI

The public CLI should remain small and intention-oriented.

Target V1:

```bash
retornatus init
retornatus wake
retornatus status
retornatus change
retornatus run
retornatus verify
retornatus inspect <id>
retornatus search <query>
retornatus doctor
```

Subcommands may be introduced when useful.

Avoid exposing every internal mechanism as a top-level command.

> **CLI should expose intentions, not internal machinery.**

---

# 63. Environment Integration

Retornatus may create environment bridge files when required.

Examples may include:

```text
.cursor/
.cursorrules

.claude/
CLAUDE.md

.codex/
AGENTS.md

.github/
copilot-instructions.md
```

These files are integration projections.

They must not become independent sources of semantic truth when the canonical information already exists in `.retornatus/`.

Environment-specific projections should be regenerable where practical.

---

# 64. Native Capability Strategy

For every capability, Retornatus should ask:

```text
Does Retornatus already solve it sufficiently?
        │
        ├── YES → preserve / refine
        │
        └── NO
             ↓
Does Environment solve it?
        │
        ├── YES → use natively
        │
        └── NO
             ↓
Is there a proven external pattern?
        │
        ├── YES → adapt
        │
        └── NO
             ↓
Design minimal mechanism
```

Examples:

If Codex provides isolated worktrees:

```text
Retornatus
↓
request isolation capability
↓
Codex Adapter
↓
native worktree
```

Do not implement a competing Retornatus worktree system.

If an Environment provides native subagents:

```text
Allocation
↓
SUBAGENTS capability
↓
Environment Adapter
↓
native subagents
```

Do not implement an Agent Pool.

---

# 65. Explicit V1 Non-Goals

Retornatus V1 must not implement the following without a demonstrated architectural failure:

- SaaS control plane;
- remote Retornatus server;
- Graph Database;
- Vector Database;
- Event Store;
- Event Journal;
- Agent Pool;
- Workspace Pool;
- permanent Reviewer Agent;
- permanent Security Agent;
- permanent Research Agent;
- Convergence Engine;
- Divergence Engine;
- Loop Engine;
- Recovery subsystem;
- Code Review subsystem;
- KnowledgeManager;
- KnowledgeEntity;
- KnowledgeStore;
- Action Strategy subsystem;
- mandatory Wave entity;
- proprietary sandbox replacing native environment isolation;
- universal Scope hierarchy;
- distributed scheduler;
- Kubernetes-style orchestration;
- automatic Rule Graduation;
- autonomous authoritative Rule creation.

---

# 66. Implementation Research Protocol

When evaluating a mechanism during implementation, follow:

```text
1. SPEC GUARDRAILS ARCHAEOLOGY
2. EXTERNAL RESEARCH
3. NATIVE CAPABILITY CHECK
4. GAP ANALYSIS
5. RETORNATUS DESIGN
6. CONVERGENCE / DIVERGENCE ANALYSIS
7. STRUCTURAL ANALYSIS
8. BOUNDARY ANALYSIS
9. CROSS-CHECK
10. STATUS → OPEN / STABLE
```

Spec Guardrails archaeology must inspect implementation, not only documentation.

Relevant surfaces may include:

- README;
- docs;
- skills;
- hub;
- references;
- CLI;
- libraries;
- Python gates;
- scripts;
- templates;
- configuration;
- state;
- memory;
- tests;
- related call chains.

For every proposed mechanism ask:

> **Does this mechanism save more complexity than it creates?**

---

# 67. Structural Analysis Protocol

Mechanisms should not automatically become independent architecture.

Use:

```text
Mechanism Discovery
        ↓
Individual Analysis
        ↓
Interaction Analysis
        ↓
Convergence / Divergence Analysis
        ↓
Structural Analysis
        ↓
Boundary Analysis
        ↓
Classification
        ↓
Grouping / Separation
        ↓
Cross-check
        ↓
Architecture Reconciliation
```

Classify concepts as appropriate:

- Subsystem;
- Mechanism;
- Entity;
- Model;
- Process;
- Projection;
- Integration Component;
- Outcome.

Ask:

- What owns it?
- What consumes it?
- What does it produce?
- Who invokes it?
- What depends on it?
- Does it have independent state?
- Does it have an independent lifecycle?
- Does it make independent decisions?
- Could it meaningfully exist without neighboring concepts?
- Does it deserve architectural independence?

> **Conceptual importance does not imply architectural independence.**

> **CONVERGENCE ≠ OWNERSHIP**

> **Don't impose the architecture on the concepts. Let the architecture emerge from their relationships.**

---

# 68. Implementation Milestones

## M0 — Foundation

Deliver:

- Python package;
- `pyproject.toml`;
- `src/retornatus/`;
- CLI bootstrap;
- `retornatus --help`;
- test infrastructure;
- basic project detection;
- `.retornatus/` initialization.

Acceptance:

```bash
uvx retornatus init
```

creates a valid minimal Retornatus project.

---

## M1 — Domain Core

Implement initial Pydantic models for:

- Change;
- Demand;
- Contract;
- Action;
- Task;
- Finding;
- Question;
- Evidence;
- Rule;
- Learning metadata;
- Authority;
- Boundaries;
- relations.

Deliver:

- schema versioning;
- identifier types;
- domain validation;
- relation vocabulary.

No Environment-specific logic.

---

## M2 — Persistence

Implement:

- Repository interfaces;
- File Repository;
- JSON serializers;
- Markdown persistence;
- TOML configuration;
- atomic writes;
- optimistic concurrency;
- migration registry.

Acceptance:

Canonical artifacts survive process interruption without partial semantic state.

---

## M3 — Change Workflow

Implement the minimum path:

```text
Demand
↓
Situation
↓
Contract
↓
Action
↓
Task? conditional
```

Deliver:

- Change creation;
- Contract activation;
- Action creation;
- Task decomposition only when needed;
- derived status.

---

## M4 — Environment and Wake Up

Implement:

- Environment identification;
- Capability Model;
- base Adapter interface;
- generic fallback Adapter;
- Wake Up;
- diagnostics.

Acceptance:

```bash
retornatus wake
```

can reconstruct relevant project state and report current Environment capabilities.

---

## M5 — Execution Context

Implement:

- Context Assembly;
- Assignment;
- stable ExecutionContext;
- relevant Rule retrieval;
- relevant Learning retrieval;
- Skill resolution;
- capability requirements;
- Authority and Boundary inclusion.

No permanent Agent identity model.

---

## M6 — Evidence and Assurance

Implement:

- Evidence creation;
- provenance;
- subject-state tracking;
- Evidence validity derivation;
- claim determination;
- required Evidence determination;
- Assurance evaluation;
- verdicts:

```text
SATISFIED
NOT_SATISFIED
INCONCLUSIVE
```

---

## M7 — Finding / Question Loop

Implement:

```text
Observation
↓
Finding
↓
Question
↓
Action
↓
Execution
↓
Evidence
↓
Assurance
↓
Resolution
```

Support:

- Question reopening;
- multiple Findings grounding a Question;
- Question resolution;
- routing significant failures through this model.

---

## M8 — Memory and Retrieval

Implement:

- Learning Markdown storage;
- SQLite derived index;
- FTS5;
- entity index;
- relation index;
- index rebuild;
- relevance-based retrieval.

Acceptance:

Deleting `retornatus.db` and running Wake Up rebuilds the index without semantic loss.

---

## M9 — Adaptation

Implement:

- Learning creation from validated experience;
- Skill Evolution workflow;
- Graduation;
- Rule Candidate creation.

No automatic authoritative Rule activation.

---

## M10 — Governance

Implement:

- Rule;
- Policy;
- Authority;
- Boundaries;
- applicability resolution;
- policy verdicts:

```text
ALLOW
DENY
REQUIRE_HUMAN
```

Support native Environment Rule realization where available.

---

## M11 — Native Environment Integration

Implement adapters incrementally according to available native capabilities.

Initial targets:

- Cursor;
- Claude Code;
- Codex.

For each Adapter:

1. identify native capabilities;
2. exploit native strengths;
3. avoid duplicate implementations;
4. generate only necessary bridge files;
5. preserve Retornatus canonical truth.

---

## M12 — End-to-End Dogfood

Use Retornatus to implement a real software Change.

The scenario must exercise:

```text
Wake Up
↓
Demand
↓
Situation
↓
Contract
↓
Action
↓
Execution
↓
Evidence
↓
Assurance
↓
Finding / Question if necessary
↓
Resolution
↓
Learning
↓
Restart
↓
Wake Up
↓
continuity
```

Dogfooding findings must be treated as engineering evidence.

Architecture should change only when concrete failure modes justify the complexity.

---

# 69. V1 Acceptance Scenario

A complete V1 should support the following scenario.

A developer enters an existing repository and runs:

```bash
uvx retornatus wake
```

Retornatus:

1. detects or initializes `.retornatus/`;
2. understands the project;
3. detects the execution Environment;
4. discovers capabilities;
5. validates canonical state;
6. rebuilds the index if necessary;
7. identifies relevant Rules and Learning;
8. reports project status.

A new Change is introduced.

Retornatus helps transform:

```text
Demand
↓
Situation
↓
Contract
↓
Action
```

The Environment executes the work using native capabilities.

Retornatus assembles sufficient Context and applies:

- Rules;
- Authority;
- Boundaries.

Execution produces attributable Evidence.

Assurance evaluates the required claims.

If a significant problem is discovered:

```text
Finding
↓
Question
↓
Action
↓
new Execution
```

When sufficient Evidence exists:

```text
Assurance
↓
SATISFIED
↓
Resolution
```

Relevant experience becomes Learning.

If Retornatus is terminated and restarted, Wake Up reconstructs continuity from repository-native durable state.

---

# 70. Success Criteria

Retornatus V1 succeeds when:

1. a software Change can move from Demand to verified outcome without relying on chat history as canonical state;
2. execution can use different AI coding environments without changing the Domain model;
3. Environment-native capabilities are exploited rather than unnecessarily recreated;
4. Contracts remain authoritative and versioned;
5. Agents operate inside applicable Rules, Authority, Context, and Boundaries;
6. Evidence is attributable;
7. Assurance can distinguish satisfied, unsatisfied, and inconclusive outcomes;
8. discovered problems can become structured Questions and Actions;
9. Learning survives across Changes;
10. authoritative Rules require Human validation;
11. Runtime can be deleted without destroying semantic history;
12. SQLite can be rebuilt from canonical files;
13. the Harness can recover after interruption;
14. simple work remains simple;
15. architectural complexity grows only in response to demonstrated failure modes.

---

# 71. Architectural Test

Before adding any new abstraction, ask:

```text
What concrete failure exists?
        ↓
Can an existing Retornatus mechanism solve it?
        ↓
Can the Environment solve it natively?
        ↓
Can a simpler established pattern solve it?
        ↓
Only then:
new mechanism
```

Reject abstractions introduced primarily because they:

- sound architecturally elegant;
- mirror another subsystem;
- anticipate hypothetical scale;
- duplicate native Environment functionality;
- convert a useful pattern into an unnecessary Engine;
- create more states than guarantees.

---

# 72. V1 Invariants

The following invariants are considered architectural requirements.

1. **Govern the work. Bound the agent. Verify the outcome.**
2. **Native first.**
3. **Govern, don't duplicate.**
4. **Preserve native advantage.**
5. **Implement only the missing capability.**
6. **A mechanism must save more complexity than it introduces.**
7. **Complexity must be earned by a concrete failure mode.**
8. **Humans and Agents express intent. Retornatus owns structure.**
9. **Files persist truth. Models validate truth. SQLite indexes and finds truth.**
10. **Durable truth must not exist only inside SQLite.**
11. **Status is a projection, not truth.**
12. **Runtime is disposable.**
13. **Execution contexts are assembled, not inherited.**
14. **Context should be sufficient, not comprehensive.**
15. **No concurrent conflicting writers.**
16. **Readiness is derived state, not durable truth.**
17. **Waves are projections, not mandatory barriers.**
18. **Parallelizable does not mean should be parallelized.**
19. **Evidence validity should be derived whenever possible.**
20. **LOG ≠ EVIDENCE.**
21. **Agent conclusion ≠ Evidence.**
22. **Independent Assurance must not inherit the author's conclusions.**
23. **A green test suite is evidence, not proof of overall correctness.**
24. **Resolution is established, not claimed.**
25. **Questions resolve locally; Memory connects historically.**
26. **Learning informs; Rules constrain.**
27. **Recurrence never creates authority automatically.**
28. **No Rule becomes authoritative without Human validation.**
29. **Rule semantics are stable; enforcement is capability-dependent.**
30. **Memory remembers; it does not decide.**
31. **Repository owns code truth; Memory owns engineering continuity.**
32. **Recovery is routing through existing semantics, not a separate architecture.**
33. **Pattern before mechanism.**
34. **Iteration without new information is repetition.**
35. **Projects depend on capabilities, not environments.**
36. **A missing native capability does not automatically become a Retornatus feature.**
37. **CLI should expose intentions, not internal machinery.**
38. **Storage format is an implementation detail; domain semantics are the contract.**
39. **Ownership is not applicability.**
40. **The narrowest sufficient boundary should win.**

---

# 73. Product Identity

The product name is:

# Retornatus

The name represents return informed by previous experience.

Retornatus does not treat iteration as blind repetition.

Its operating cycle preserves Evidence, Memory, and Learning so that subsequent work can begin from a better-informed state.

Conceptually:

```text
Intent
↓
Action
↓
Execution
↓
Evidence
↓
Assurance
↓
Learning
↓
Return
↓
Next iteration
```

The return is not a reset.

It is continuity.

---

# 74. Final Architecture

```text
                         RETORNATUS
                              │
        ┌─────────────────────┼──────────────────────┐
        │                     │                      │
        ↓                     ↓                      ↓
 PROJECT CONTINUITY       GOVERNANCE             ENVIRONMENT
        │                     │                      │
      Memory              ├─ Rule                ├─ Wake Up
                          ├─ Policy              ├─ Capability Model
                          ├─ Authority           └─ Adapter
                          └─ Boundaries
                              │
                              │
                              ↓
                            CHANGE
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ↓                    ↓                    ↓
   UNDERSTANDING           ACTION              ASSURANCE
         │                    │                    │
      Demand              Action              Evidence
      Situation             │                 Assurance
      Contract              └─ Task              │
                              │                   ↓
                              ↓               Resolution
                          Execution
                              │
                    ┌─────────┴─────────┐
                    ↓                   ↓
                 Finding             Evidence
                    │
                 Question
                    │
                  Action
                             
                              ↓
                         ADAPTATION
                              │
                   ┌──────────┼──────────┐
                   ↓          ↓          ↓
                Learning    Skill    Graduation
                                         │
                                  Rule Candidate
                                         │
                                   Human Decision
                                         │
                                        Rule
```

---

# 75. Final Principle

Retornatus exists to make AI-assisted software engineering more governable without making it unnecessarily more complicated.

It should preserve intent, constrain execution where necessary, exploit native capabilities, demand attributable evidence, establish sufficient assurance, preserve useful experience, and improve future work.

It must remain willing to stay simple.

> **Govern the work. Bound the agent. Verify the outcome.**

> **Return with evidence. Continue with learning.**

> **Govern the work. Preserve the evidence. Learn from experience. Exploit the environment. Add complexity only when reality earns it.**