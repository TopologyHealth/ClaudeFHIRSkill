---
description: Generate comprehensive test cases for FHIR resources and APIs
---

You are generating FHIR test cases. Follow these steps:

1. **Identify test scope**:
   - Unit tests for resource validation
   - Integration tests for API endpoints
   - Test fixtures (example resources)
   - End-to-end workflow tests
   - Profile conformance tests
2. **Determine test framework**:
   - Python: pytest, unittest
   - TypeScript/JavaScript: Jest, Mocha, Vitest
   - Other languages as appropriate
3. **Identify what to test**:
   - Resource creation and validation
   - CRUD operations (Create, Read, Update, Delete)
   - Search functionality with various parameters
   - Batch/transaction bundles
   - Error handling and OperationOutcome responses
   - Profile conformance (required elements, cardinality)
   - Terminology validation
4. **Generate test code**:
   - Include imports and setup
   - Create realistic test fixtures
   - Write positive test cases (valid scenarios)
   - Write negative test cases (error scenarios)
   - Add assertions for all critical properties
   - Include helpful test descriptions
5. **Write test files**: Use Write tool to create test files

**Test patterns to include**:

**Resource validation tests**:
```python
def test_valid_patient():
    # Test valid resource passes validation

def test_missing_required_field():
    # Test missing required element fails

def test_invalid_date_format():
    # Test improper date format is rejected
```

**API endpoint tests**:
```python
async def test_create_patient():
    # POST /Patient returns 201 with location header

async def test_read_patient():
    # GET /Patient/{id} returns 200 with resource

async def test_update_patient():
    # PUT /Patient/{id} returns 200

async def test_delete_patient():
    # DELETE /Patient/{id} returns 204

async def test_patient_not_found():
    # GET invalid ID returns 404 with OperationOutcome
```

**Search tests**:
```python
async def test_search_by_name():
    # GET /Patient?name=Smith returns matching patients

async def test_search_with_include():
    # GET /Observation?_include=Observation:patient includes patient resources

async def test_search_pagination():
    # Test _count and next link functionality
```

**Profile conformance tests**:
```python
def test_us_core_patient_required_elements():
    # Verify identifier, name, gender present

def test_must_support_elements():
    # Check all must-support elements are handled
```

**Test fixtures to generate**:
- Valid resource examples
- Invalid resource examples (for negative tests)
- Edge cases (empty strings, null values, boundary dates)
- Bundle examples for transaction tests

**Coverage areas**:
- Happy path scenarios
- Error conditions (400, 404, 422, 500)
- Validation failures
- Boundary conditions
- Concurrent operations
- Large datasets/pagination

**Use Write tool to create**:
- test_*.py or *.test.ts files
- fixtures/data files with example resources
- conftest.py or test setup files with shared fixtures
