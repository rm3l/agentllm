---
description: Create comprehensive plan for development tasks
argument-hint: [task-description]
model: sonnet
---

# Generic Planning Command for B4Racing

This command handles creating comprehensive plans for any development task in the B4Racing telemetry analysis monorepo, including packages, analyzers, data sources, and features.

## Usage

When this command is invoked, it will guide you through a structured 3-step planning process for any development task. Once planning is complete and approved, use the `/implement` command to execute the plan.

**Key Documentation:**
- **Architecture Overview**: See `docs/architecture/README.md` for system design and patterns
- **Development Guides**: See `docs/guides/README.md` for practical how-tos

## The 3-Step Planning Process

### Step 1: Requirements Gathering
- **Understand the task:** What exactly needs to be accomplished?
- **Analyze visual specifications:** If provided (screenshots, mockups), identify sections, metrics, visualizations
- **Gather context:** What existing systems/files are involved?
- **Check existing components:** Review implementation status to avoid duplication
- **Identify constraints:** What limitations or requirements exist?
- **Define success criteria:** How will we know the task is complete?
- **Clarify scope:** What is in-scope vs out-of-scope?

### Step 2: Create Planning Document
- **Create plan document** in `specs/plans/<task_name>.md`
- **Document requirements** gathered in Step 1
- **Analyze current state** of relevant systems
- **Map to architecture components** (packages, analyzers, data sources, plugins)
- **Identify dependencies** and prerequisites
- **Draft implementation approach** with architecture alignment
- **Plan testing strategy** (unit tests, integration tests)

### Step 3: Refine Planning Document (MANDATORY REVIEW & ITERATION)
- **Present the plan** to the user for review
- **Gather feedback** and make adjustments
- **Iterate on the plan file** until user is satisfied
- **Update the plan document** with each round of feedback
- **Ensure all requirements** are captured accurately
- **Validate approach** with user's expectations
- **Get explicit greenlight** from user before considering plan complete
- ⚠️ **CRITICAL**: Once greenlight is received, inform user to use `/implement` command

## B4Racing-Specific Planning Knowledge

### System Architecture Overview

The B4Racing system is a **monorepo** with independently versioned packages using plugin architecture:

```
Data Sources → Telemetry Processing → Analysis → Graphics → Reports
```

**Key Packages:**
- **Core**: Domain models (Session, Telemetry, Lap)
- **Source**: Data source implementations (iRacing, Garage61, filesystem)
- **Telemetry**: Processing, normalization, caching
- **Metadata**: Game, track, car information
- **Analysis**: Analyzers and graphics (plugins via entry points)
- **CLI**: Command-line interface

**See `docs/architecture/README.md` for detailed architecture documentation.**

### Planning for New Analyzers

When planning a new analyzer:

**Research Phase:**
- Check `specs/plans/monorepo-index.md` for implementation status
- Review existing analyzers in `packages/analysis/src/b4racing/analysis/analyzers/`
- Identify required telemetry channels
- Determine slice type needed (lap, stage, etc.)

**Implementation Approach:**
- Use `BaseAnalyzer` class from `packages/analysis/`
- Define TypedDict contracts for options and results
- Register via entry point in `pyproject.toml`
- Write tests using pytest fixtures

**See `docs/guides/adding-analyzers.md` for detailed guide.**

### Planning for New Data Sources

When planning a new data source:

**Research Phase:**
- Check `specs/plans/monorepo-index.md` for existing sources
- Review existing sources in `packages/source-*/`
- Identify telemetry format and metadata availability

**Implementation Approach:**
- Implement `DataSourceProtocol` from `packages/source/`
- Handle column normalization and unit conversion
- Support both telemetry loading and metadata fetching
- Create package with PyScaffold: `putup packages/source-mysource --namespace b4racing --b4racing`

**See `docs/guides/adding-data-sources.md` for detailed guide.**

### Planning for New Graphics

When planning graphics analyzers:

**Research Phase:**
- Check existing graphics in `packages/analysis/src/b4racing/analysis/graphics/`
- Determine graphic type (line chart, scatter plot, track map, etc.)
- Identify required data and telemetry channels

**Implementation Approach:**
- Use `GraphicAnalyzer` base class (adapter for `BaseAnalyzer`)
- Register via entry point in `packages/analysis/pyproject.toml`
- Return graphic output (PNG/SVG) in result

**See `docs/guides/adding-analyzers.md` section on graphics analyzers.**

## Architecture Compliance Checklist

Before creating the plan, verify:

### Foundation Documents
- ✅ Read `docs/architecture/README.md` for system overview
- ✅ Check `specs/plans/monorepo-index.md` for implementation status
- ✅ Review `docs/guides/README.md` for practical guides
- ✅ Consult package-specific `CLAUDE.md` files for package patterns

### Component Discovery
- ✅ Check if required analyzers exist before planning new ones
- ✅ Check if required data sources exist before planning new ones
- ✅ Check if required graphics exist before planning new ones
- ✅ Identify existing protocols to implement

### Design Principles
- ✅ **Protocol-Oriented Design**: Protocols co-located with implementations
- ✅ **Progressive Enhancement**: Components adapt to data availability
- ✅ **Plugin Architecture**: Use entry points for extensibility
- ✅ **PEP 420 Namespaces**: All packages use `b4racing.*` namespace
- ✅ **Independent Packages**: Clear boundaries and versioning

### Testing Strategy
- ✅ **Unit Tests**: Per-package tests with pytest
- ✅ **Integration Tests**: Cross-package tests in workspace
- ✅ **Fixtures**: Shared synthetic data in `tests/fixtures/`

## Next Steps: Implementation

Once the plan is approved (greenlight received), the user should run:

```bash
/implement specs/plans/<plan-name>.md
```

The `/implement` command will:
- Execute the implementation following the approved plan
- Track progress across one or multiple sessions
- Maintain an implementation log at `specs/plans/<plan-name>-implementation.md`
- Handle testing, documentation, and final reporting

## Workflow

When this command is invoked:

1. **Analyze the request:**
   - Is it a new package, analyzer, data source, or graphics?
   - Is it a modification to existing component?
   - Is it a feature addition (CLI command, protocol, etc.)?
   - What packages will be affected?

2. **Ask clarifying questions:**
   ```
   I'll help you plan this task. Let me gather some information:

   [Ask specific questions based on task type:]
   - What is the primary goal of this feature/component?
   - What are the key requirements and constraints?
   - What packages will be affected?
   - Are there existing components that can be reused?
   - What priority level (nice-to-have vs critical)?
   ```

3. **Execute Step 1: Requirements Gathering**
   - **Review architecture documentation**:
     - Start with `docs/architecture/README.md` for system overview
     - Check `specs/plans/monorepo-index.md` for implementation status
     - Review `docs/guides/README.md` for relevant guides
   - **Analyze existing components:**
     - Search for similar packages/analyzers/sources
     - Check available protocols in package protocol files
     - Review test patterns in existing packages
   - Ask clarifying questions based on the task type
   - Identify potential challenges or blockers
   - Confirm understanding with the user

4. **Execute Step 2: Create Planning Document**
   Generate comprehensive plan in `specs/plans/` with sections:

   ```markdown
   # [Feature Name] - Implementation Plan

   ## Overview
   - **Goal**: [Clear objective]
   - **Type**: [Package/Analyzer/Data Source/Graphics/Feature]
   - **Packages Affected**: [List of packages]
   - **Priority**: [High/Medium/Low]

   ## Requirements
   [From Step 1 - detailed requirements]

   ## Architecture Alignment

   ### Existing Components to Use
   - **Packages**: [List with paths]
   - **Analyzers**: [List with paths]
   - **Data Sources**: [List with paths]
   - **Graphics**: [List with paths]

   ### New Components Required
   - **Packages**: [List with rationale]
   - **Analyzers**: [List with rationale]
   - **Data Sources**: [List with rationale]
   - **Graphics**: [List with rationale]

   ### Protocols to Implement
   - [List of protocols from package protocol files]

   ## Implementation Approach

   ### Phase 1: [Component 1]
   [Detailed steps following appropriate workflow]

   ### Phase 2: [Component 2]
   [Detailed steps following appropriate workflow]

   ### Phase 3: [Integration]
   [How components fit together]

   ## Testing Strategy

   ### Unit Tests
   [For analyzers - TDD approach]

   ### Integration Tests
   [For reports/templates]

   ### Validation Criteria
   [Success criteria from Step 1]

   ## Files to Create/Modify

   ### New Files
   - `path/to/new/file.py` - [Purpose]

   ### Modified Files
   - `path/to/existing/file.py` - [Changes]

   ## Dependencies & Prerequisites
   - [List of dependencies]
   - [Required data/setup]

   ## Risks & Mitigations
   - **Risk**: [Description]
     - **Mitigation**: [Strategy]

   ## Timeline Estimate
   [Rough estimate of implementation phases]

   ## Success Criteria
   - ✅ [Criterion 1]
   - ✅ [Criterion 2]
   ```

5. **Execute Step 3: Refine Planning Document**
   - Present plan to user for review
   - Incorporate feedback and update the plan file
   - Iterate multiple times if needed
   - Continue refining until user explicitly greenlights
   - ⚠️ Once greenlight received, inform user to use `/implement` command

6. **Planning Complete**
   - Confirm plan document is saved and finalized
   - Direct user to run `/implement specs/plans/<plan-name>.md` to begin implementation

## Best Practices

### For Requirements Gathering
- Ask open-ended questions to understand the "why" behind requests
- Explore edge cases and error conditions
- Consider integration with existing systems
- Validate assumptions with the user
- Document all requirements clearly in the plan
- **For visual specs**: Systematically analyze every section and visualization

### For Planning Documents
- Be specific and actionable in plans
- Include concrete examples where helpful
- Consider both happy path and error scenarios
- Make plans reviewable and updateable
- Structure plans to be implementation-ready
- Include clear success criteria and testing approach
- **Reference existing code**: Provide file:line references to similar implementations
- **Map to architecture**: Show how new components fit into existing structure

### For Plan Review and Iteration
- Present plans clearly with organized sections
- Be open to feedback and willing to iterate
- Ask clarifying questions if feedback is unclear
- Update the plan document with each round of changes
- Ensure user explicitly approves before considering complete
- Document any assumptions or decisions made during planning

### For Architecture Alignment
- Always consult `docs/architecture/README.md` before creating plans
- Check `specs/plans/monorepo-index.md` to avoid duplicating existing components
- Review `docs/guides/README.md` for relevant implementation guides
- Follow established patterns (protocols, progressive enhancement, plugin architecture)
- Ensure plans align with monorepo structure and package boundaries
- Note in plan if new architecture patterns are being introduced

### For Package Planning
- Use PyScaffold with `--b4racing` extension for new packages
- Follow PEP 420 namespace conventions (`b4racing.*`)
- Plan clear package boundaries and dependencies
- Consider versioning and release strategy
- Include package-level tests and documentation

### For Analyzer Planning
- Use `BaseAnalyzer` class from `packages/analysis/`
- Define TypedDict contracts for options and results
- Plan for progressive enhancement (metadata-only support)
- Register via entry points in `pyproject.toml`
- Write tests using pytest fixtures

### For Data Source Planning
- Implement `DataSourceProtocol` from `packages/source/`
- Plan column normalization and unit conversion
- Support both telemetry loading and metadata fetching
- Handle errors and missing data gracefully
- Test with VCR cassettes for API sources

### For Graphics Planning
- Use `GraphicAnalyzer` base class from `packages/analysis/graphics/`
- Check if existing graphics can be reused/extended
- Return graphic output (PNG/SVG) in result
- Consider performance with large datasets

## Example Usage Scenarios

### New Data Source
```
User: "Add support for ACC telemetry files"
Plan Command:
1. Checks existing sources in packages/source-*/
2. Reviews ACC file format and available data
3. Plans new package: packages/source-acc
4. Plans column normalization and unit conversion
5. Plans tests with sample ACC files
```

### New Analyzer
```
User: "Create a throttle application analyzer"
Plan Command:
1. Checks existing analyzers in packages/analysis/
2. Reviews BaseAnalyzer pattern
3. Defines contracts (ThrottleOptions, ThrottleAnalyzerResult)
4. Plans implementation with required channels
5. Plans entry point registration and tests
```

### New Graphics Analyzer
```
User: "Add track map with racing line visualization"
Plan Command:
1. Checks existing graphics in packages/analysis/graphics/
2. Reviews GraphicAnalyzer pattern
3. Identifies data requirements (position coordinates, racing line)
4. Plans TrackMapAnalyzer implementation
5. Plans entry point registration and visual tests
```

### New Package
```
User: "Create a package for export functionality to different formats"
Plan Command:
1. Reviews monorepo structure and package organization
2. Plans new package: packages/export
3. Defines protocols for exporters (ExporterProtocol)
4. Plans plugin architecture for format handlers
5. Plans CLI integration and tests
```

## Common Pitfalls to Avoid

❌ **Assuming components exist**: Always check `specs/plans/monorepo-index.md` first
❌ **Planning without architecture review**: Always consult `docs/architecture/README.md`
❌ **Creating new packages unnecessarily**: Check for reusable packages first
❌ **Vague requirements**: Be specific about requirements and constraints
❌ **Ignoring progressive enhancement**: Consider metadata-only scenarios
❌ **Forgetting entry point registration**: Plan plugin registration for analyzers/graphics
❌ **No testing strategy**: Every component needs tests planned upfront
❌ **Wrong namespace**: All packages must use `b4racing.*` namespace

## Quick Reference

### Key Documentation
- `docs/architecture/README.md` - System overview and architecture
- `docs/guides/README.md` - Practical implementation guides
- `specs/plans/monorepo-index.md` - Implementation status tracker
- Package `CLAUDE.md` files - Per-package instructions

### Key Directories
- `packages/` - Core packages (core, telemetry, source, metadata, analysis)
- `packages/source-*/` - Data source implementations
- `packages/analysis/src/b4racing/analysis/analyzers/` - Analyzers
- `packages/analysis/src/b4racing/analysis/graphics/` - Graphics analyzers
- `tests/fixtures/` - Shared test fixtures
- `specs/plans/` - Planning documents

### Verification Commands
```bash
# Check implementation status
cat specs/plans/monorepo-index.md

# Check existing analyzers
fd -e py . packages/analysis/src/b4racing/analysis/analyzers

# Check existing graphics
fd -e py . packages/analysis/src/b4racing/analysis/graphics

# Check data sources
ls -d packages/source-*/

# Run tests
nox -s test_all
```

## Version

This planning command reflects the B4Racing monorepo as of **2025-11-04** and should be updated when architecture or workflows change.
