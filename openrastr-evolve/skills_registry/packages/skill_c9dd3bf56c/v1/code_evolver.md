# Skill: Code Evolver

## Category
Scaffolding + Verification + Automation

## Intent
Continuously generate, refine, validate, and improve code until it meets functional, structural, and quality standards.

This skill does not stop at generation.
It evolves code through iterative improvement and verification loops.

## Responsibilities
- Generate initial code from intent
- Refactor and optimize existing code
- Validate correctness through tests and assertions
- Enforce coding standards
- Iterate until quality thresholds are met

## Inputs

### Required
- user_request: string

### Optional
- language: string
- framework: string
- existing_code: string
- constraints: list
- quality_level: basic | production | enterprise
- include_tests: boolean (default: true)

## Reference Knowledge

### APIs & Libraries
- Language-specific standard libraries
- Framework best practices
- Testing frameworks:
  - pytest
  - unittest
  - jest

## Datasets & Queries

### Internal Queries
- best practices for language
- common bugs in framework
- optimization patterns

### Signals Used
- code complexity
- readability score
- test coverage
- error patterns

## Executable Workflow

### Step 1: Interpret Intent
- Extract requirements
- Identify type

### Step 2: Initial Code Generation
- Generate baseline working code

### Step 3: Static Review
- Check syntax and structure

### Step 4: Enhancement Pass
- Improve readability and performance

### Step 5: Test Generation
- Generate unit tests

### Step 6: Execution Simulation
- Validate logic consistency

### Step 7: Iterative Evolution Loop
- Detect issues
- Refine code
- Re-run tests

### Step 8: Finalization
- Clean formatting
- Add documentation

## Output
- Final evolved code
- Unit tests (if enabled)

## Constraints
- Must be executable
- Follow best practices
- Maintain clarity

## Verification Rules
- Must pass test cases
- No dead code
- Clear input/output

## Automation Hooks
- test_runner_skill
- code_linter_skill
- formatter_skill

## Quality Levels

### Basic
- Working code

### Production
- Error handling
- Tests

### Enterprise
- Modular design
- High coverage

## Prompt Template

You are a senior software engineer.

User Request:
{user_request}

Existing Code:
{existing_code}

Process:
1. Generate code
2. Review and refine
3. Add tests
4. Validate logic
5. Repeat until high quality

Return only final code.
