# Skill: Verification Engine

## Category
Verification + Quality Assurance

## Intent
Validate, test, and ensure that generated outputs (code, markdown, data transformations) are correct, complete, and aligned with user intent.

This skill acts as the gatekeeper before any output is accepted.

---

## Responsibilities
- Validate functional correctness
- Ensure completeness of output
- Detect logical and structural errors
- Enforce standards and best practices
- Provide feedback for refinement loops

---

## Inputs

### Required
- generated_output: string
- original_request: string

### Optional
- expected_format: string
- validation_rules: list
- context: string

---

## Reference Knowledge

### Standards
- Language best practices
- Markdown formatting rules
- Data structure validation patterns

### Testing Framework Concepts
- Unit testing principles
- Edge case coverage
- Input/output validation

---

## Datasets & Queries

### Internal Queries
- "common failure cases for {task}"
- "edge cases for {problem_type}"
- "format validation rules"

### Signals Used
- completeness score
- correctness score
- readability score
- structural consistency

---

## Executable Workflow

### Step 1: Intent Matching
- Compare generated_output with original_request
- Ensure all requirements are addressed

---

### Step 2: Structural Validation
- Check formatting (code / markdown / data)
- Verify hierarchy and organization

---

### Step 3: Completeness Check
- Ensure no missing components
- Validate all entities are covered

---

### Step 4: Logical Validation
- Check consistency and correctness
- Detect contradictions or invalid logic

---

### Step 5: Edge Case Testing
- Identify potential failure scenarios
- Simulate inputs mentally

---

### Step 6: Standards Enforcement
- Apply best practices
- Remove anti-patterns

---

### Step 7: Scoring

Assign scores (0–1):

- correctness_score
- completeness_score
- readability_score
- structure_score

Final Score = weighted average

---

### Step 8: Decision

If score >= threshold:
- PASS

Else:
- FAIL
- Generate feedback for refinement

---

## Output

### Pass Case
- status: PASS
- confidence_score: float

### Fail Case
- status: FAIL
- issues: list
- suggestions: list

---

## Constraints

- Must not hallucinate missing requirements
- Must be strict on correctness
- Prefer precision over leniency

---

## Verification Rules

- Output must match intent
- No missing critical components
- Clear structure and readability
- No logical inconsistencies

---

## Automation Hooks

- Can trigger code_evolver.md for fixes
- Can integrate with test runners
- Can connect to linting tools

---

## Prompt Template

You are a strict verification engine.

Original Request:
{original_request}

Generated Output:
{generated_output}

Tasks:
1. Check correctness
2. Check completeness
3. Validate structure
4. Identify issues
5. Assign score

Return:
- PASS or FAIL
- Detailed issues if any
- Suggestions for improvement
