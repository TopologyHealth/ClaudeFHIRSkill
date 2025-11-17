---
description: Generate a FHIR resource template with proper structure and example data
---

You are creating a FHIR resource template. Follow these steps:

1. **Identify requirements**:
   - Resource type (Patient, Observation, Medication, etc.)
   - FHIR version (R4, R4B, R5) - default to R4 if not specified
   - Profile to conform to (e.g., US Core, base FHIR)
   - Include must-support elements only or full example
2. **Determine target language/format**:
   - JSON (default)
   - TypeScript interface
   - Python Pydantic model
   - Plain JSON template
3. **Generate the resource**:
   - Include all required elements
   - Add must-support elements if profile specified
   - Use realistic example data
   - Include helpful comments explaining key elements
   - Add proper typing/validation if generating code
4. **Write the file**: Use the Write tool to create the file with appropriate extension (.json, .ts, .py)

**Resource structure guidelines**:
- Always include resourceType
- Add id for examples
- Include meta.profile array if conforming to specific profile
- Use proper date/datetime formats (YYYY-MM-DD, YYYY-MM-DDThh:mm:ss+zz:zz)
- Include proper identifier systems
- Use realistic code systems (LOINC, SNOMED CT, RxNorm)

**For code generation**:
- TypeScript: Use proper FHIR type imports from @types/fhir
- Python: Use fhir.resources library with proper imports
- Include validation logic and type safety

**Example templates to offer**:
- Patient with name, gender, birthDate, identifier
- Observation with code, value, subject reference
- Medication with code, form, ingredient
- Condition with code, subject, onset
- Bundle for batch/transaction operations
