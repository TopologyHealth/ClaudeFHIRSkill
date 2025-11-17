---
description: Help construct FHIR search queries with proper parameters and syntax
---

You are helping construct a FHIR search query. Follow these steps:

1. **Understand the search requirements**:
   - Resource type to search (Patient, Observation, etc.)
   - Search criteria (name, date, code, status, etc.)
   - Target system (generic FHIR server, Epic, Cerner, etc.)
   - Output format needed (URL, curl command, code snippet)
2. **Identify search parameters**:
   - Look up valid search parameters for the resource type
   - Determine parameter type (string, token, date, reference, quantity)
   - Check if parameters are standard or custom
3. **Construct the query**:
   - Build proper URL with query parameters
   - Use correct search parameter syntax:
     - String: `?name=John` (partial match), `?name:exact=John` (exact)
     - Token: `?code=http://loinc.org|12345-6` (system|code)
     - Date: `?date=ge2024-01-01` (>=), `?date=lt2024-12-31` (<)
     - Reference: `?subject=Patient/123`
     - Composite: Multiple parameters combined
   - Add modifiers (_include, _revinclude, _sort, _count, _summary)
4. **Provide the query in requested format**:
   - REST URL: `GET [base]/Patient?name=Smith&birthdate=ge1990-01-01`
   - curl command with proper headers
   - Code snippet (Python requests, TypeScript fetch, etc.)
5. **Explain the query**: Describe what each parameter does

**Common search patterns**:
- Search by identifier: `?identifier=http://hospital.org|12345`
- Search by token with system: `?code=http://loinc.org|8867-4`
- Date range: `?date=ge2024-01-01&date=le2024-12-31`
- Include references: `?_include=Observation:patient`
- Reverse include: `?_revinclude=Observation:subject`
- Chained parameters: `?subject:Patient.name=Smith`
- Sort results: `?_sort=-date` (descending)
- Pagination: `?_count=50&_offset=0`

**Search result bundles**:
- Explain Bundle.type = searchset
- Show how to parse entry array
- Explain pagination links (next, previous, self)

**Provide examples for common use cases**:
- Find patient by name and birthdate
- Get recent observations for a patient
- Search medications by code
- Find conditions with specific onset date range
