---
description: Validate a FHIR resource file against a profile or the base FHIR specification
---

You are validating a FHIR resource. Follow these steps:

1. **Identify the resource**: Ask the user which file or resource to validate if not specified
2. **Determine validation target**:
   - Base FHIR specification (R4, R4B, or R5)
   - Specific profile URL (e.g., US Core Patient)
   - Implementation Guide
3. **Read the resource file** using the Read tool
4. **Perform validation checks**:
   - Verify resourceType is valid
   - Check required fields are present
   - Validate data types (dates, codes, references)
   - Check cardinality constraints (min/max)
   - Verify coding/CodeableConcept against terminology bindings if profile specified
   - Validate extensions against their definitions
5. **Report results**:
   - List all validation errors with severity (error/warning)
   - Show the specific element path that failed
   - Provide actionable suggestions to fix issues
   - If valid, confirm compliance

**Output format**: Provide a clear OperationOutcome-style report with issue severity, code, and details.

**Tools to use**:
- Read tool to load the resource file
- Reference the FHIR specification and profile definitions from the skill knowledge
- For complex profile validation, suggest using the official FHIR validator CLI

**Example issues to check**:
- Missing required elements (Patient.name, Patient.identifier for US Core)
- Invalid date formats (must be YYYY-MM-DD)
- Invalid reference formats (must be ResourceType/id)
- Codes not in required ValueSets
- Cardinality violations (e.g., max 1 but multiple values present)
