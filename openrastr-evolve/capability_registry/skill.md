
# Capability Registry

Each capability defines:
- name
- description
- llm_backend
- input_schema
- output_schema
- dependencies

---

## Capability: Longitudinal Data Analysis
llm_backend: mistral:latest
description: Analyze time-series healthcare claims and clinical events.
input_schema:
  claims_data: table
  clinical_events: table
output_schema:
  patient_timelines: array
dependencies:
  - Claims Data Transformation

---

## Capability: Claims Data Transformation
llm_backend: llama3:latest
description: Convert raw claims datasets into structured format.
input_schema:
  raw_claims_records: array
output_schema:
  structured_claims: table
dependencies:
  - None

---

## Capability: NLP for Clinical Event Extraction
llm_backend: qwen:4b
description: Extract diagnoses and clinical events from records.
input_schema:
  clinical_notes: text
output_schema:
  clinical_events: array
dependencies:
  - None

---

## Capability: SLM Agent Evaluation
llm_backend: qwen:4b
description: Evaluate patient progression pathways.
input_schema:
  patient_timelines: array
output_schema:
  pathway_scores: array
dependencies:
  - Longitudinal Data Analysis

---

## Capability: Historical Pattern Comparison
llm_backend: mistral:latest
description: Compare patient pathways with historical cohorts.
input_schema:
  pathway_scores: array
output_schema:
  anomaly_flags: array
dependencies:
  - SLM Agent Evaluation

---

## Capability: Risk Prediction Modeling
llm_backend: mistral:latest
description: Predict future patient risk scores.
input_schema:
  patient_features: array
output_schema:
  risk_scores: array
dependencies:
  - Historical Pattern Comparison

---

## Capability: Proactive Intervention Recommendation
llm_backend: llama3:latest
description: Generate recommended payer interventions.
input_schema:
  risk_scores: array
output_schema:
  intervention_recommendations: array
dependencies:
  - Risk Prediction Modeling


---

## Capability: Clinical data processing
llm_backend: Python
description: A Python module for clinical data processing, including the ability to process longitudinal data and generate proactive care intervention recommendations.
input_schema:
  generated_payload: object
output_schema:
  generated_result: object
dependencies:
  - pandas
module_path: deep_pipeline/generated_capabilities/clinical_data_processing.py

---

## Capability: Code Evolver
llm_backend: mistral:latest
description: Continuously generate, refine, validate, and improve code until it meets functional, structural, and quality standards.
input_schema:
  user_request: dynamic
  language: dynamic
  framework: dynamic
  existing_code: dynamic
  constraints: dynamic
  quality_level: dynamic
  include_tests: dynamic
output_schema:
  final_evolved_code: dynamic
  unit_tests: dynamic
dependencies:
  - None
tags: scaffolding, verification, automation, code-generation, refactoring


---

## Capability: Verification Engine
llm_backend: mistral:latest
description: Validate, test, and ensure that generated outputs are correct, complete, and aligned with user intent.
input_schema:
  generated_output: dynamic
  original_request: dynamic
  expected_format: dynamic
  validation_rules: dynamic
  context: dynamic
output_schema:
  status: dynamic
  confidence_score: dynamic
  issues: dynamic
  suggestions: dynamic
dependencies:
  - None
tags: verification, quality-assurance, validation, testing


---

## Capability: Parse structured ontology formats (RDF, OWL, JSON-LD)
llm_backend: codellama:latest
description: Auto-generated capability module for Parse structured ontology formats (RDF, OWL, JSON-LD).
input_schema:
  generated_payload: object
output_schema:
  generated_result: object
dependencies:
  - Code Evolver
module_path: deep_pipeline/generated_capabilities/parse_structured_ontology_formats_rdf_owl_json_ld.py


---

## Capability: Convert parsed ontology data into Markdown format
llm_backend: Python
description: Reusable Python module for converting parsed ontology data into Markdown format.
input_schema:
  generated_payload: object
output_schema:
  generated_result: object
dependencies:
  - rdflib
module_path: deep_pipeline/generated_capabilities/convert_parsed_ontology_data_into_markdown_format.py
