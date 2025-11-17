# FHIR Search Parameters and API Patterns Reference

This document provides comprehensive guidance on implementing FHIR search functionality and API patterns.

## FHIR Search Parameter Types

### 1. String Parameters
Search on string fields with prefix matching and case-insensitive behavior.

**Examples:**
- `GET /Patient?name=john` - Find patients with "john" in any name component
- `GET /Patient?family=doe` - Search by family name
- `GET /Organization?name:exact=ACME Corp` - Exact string match

**Modifiers:**
- `:exact` - Exact case-sensitive match
- `:contains` - Substring search
- `:missing` - Search for missing/present values

### 2. Token Parameters
Search on coded values, identifiers, and boolean fields.

**Format:** `[system]|[code]`

**Examples:**
- `GET /Patient?identifier=123456` - Patient with identifier value
- `GET /Patient?identifier=http://hospital.org|123456` - With specific system
- `GET /Observation?code=http://loinc.org|55284-4` - Specific LOINC code
- `GET /Patient?active=true` - Boolean search

**Modifiers:**
- `:text` - Search in display text
- `:not` - Negation
- `:above` / `:below` - Code hierarchy navigation

### 3. Date/DateTime Parameters
Search on date and dateTime fields with precision handling.

**Examples:**
- `GET /Patient?birthdate=1990` - Born in 1990
- `GET /Patient?birthdate=ge2020-01-01` - Born on or after Jan 1, 2020
- `GET /Observation?date=2023-03-15` - Observations on specific date

**Prefixes:**
- `eq` - Equal (default)
- `ne` - Not equal
- `gt` - Greater than
- `lt` - Less than
- `ge` - Greater or equal
- `le` - Less or equal
- `sa` - Starts after
- `eb` - Ends before
- `ap` - Approximately

### 4. Number Parameters
Search on numeric values with precision and range support.

**Examples:**
- `GET /Observation?value-quantity=5.4` - Value equals 5.4
- `GET /Observation?value-quantity=gt100` - Value greater than 100
- `GET /RiskAssessment?probability=lt0.8` - Probability less than 0.8

### 5. Reference Parameters
Search by references to other resources.

**Examples:**
- `GET /Observation?subject=Patient/123` - References specific patient
- `GET /Observation?subject:Patient=123` - Type-specific reference
- `GET /DiagnosticReport?result=Observation/456` - References observation

**Chaining:**
- `GET /Observation?subject.name=smith` - Chain to referenced resource
- `GET /DiagnosticReport?subject:Patient.birthdate=1990` - Chain with type

### 6. Quantity Parameters
Search on Quantity values with units and comparisons.

**Format:** `[prefix][number]|[system]|[code]`

**Examples:**
- `GET /Observation?value-quantity=5.4|http://unitsofmeasure.org|mg`
- `GET /Observation?value-quantity=gt100||mg` - Greater than 100mg
- `GET /Observation?value-quantity=ap5.4` - Approximately 5.4

### 7. Composite Parameters
Search on multiple related fields simultaneously.

**Examples:**
- `GET /Observation?code-value-quantity=http://loinc.org|33747-0$gt5.4|http://unitsofmeasure.org|mmol/L`
- `GET /Observation?component-code-value-quantity=...` - Component values

## Search Modifiers

### Universal Modifiers
- `:missing=true|false` - Search for missing/present values
- `:exact` - Exact string matching
- `:contains` - Substring search
- `:text` - Search in human-readable text

### Reference Modifiers
- `:identifier` - Search by identifier instead of ID
- `:[type]` - Type-specific reference search
- `:iterate` - Follow reference chains

### String Modifiers
- `:exact` - Case-sensitive exact match
- `:contains` - Case-insensitive substring

## Search Result Parameters

### Pagination
```
GET /Patient?_count=20&_offset=40
GET /Patient?_page=3&_count=20
```

### Include/Reverse Include
```
GET /DiagnosticReport?_include=DiagnosticReport:subject
GET /Patient?_revinclude=Observation:subject
GET /Patient?_include=Patient:organization&_include:iterate=Organization:partof
```

### Sorting
```
GET /Patient?_sort=family
GET /Patient?_sort=birthdate,-family  # Multiple sort, desc family
GET /Observation?_sort=date:desc
```

### Element Selection
```
GET /Patient?_elements=id,name,birthDate
GET /Patient?_summary=true
GET /Patient?_summary=text
GET /Patient?_summary=data
```

### Format Control
```
GET /Patient?_format=json
GET /Patient?_format=xml
GET /Patient?_format=application/fhir+json
```

## Advanced Search Patterns

### Composite Searches
Combine multiple parameters with AND logic:
```
GET /Patient?name=smith&birthdate=1990&active=true
```

### OR Logic with Multiple Values
```
GET /Patient?name=smith,jones,wilson
GET /Observation?code=http://loinc.org|12345,http://loinc.org|67890
```

### Complex Date Ranges
```
GET /Observation?date=ge2023-01-01&date=lt2023-02-01
GET /Patient?birthdate=ge1990&birthdate=le1995
```

### Chained Searches
```
GET /DiagnosticReport?subject.gender=female
GET /Observation?subject:Patient.name=smith
GET /MedicationRequest?patient.identifier=123456
```

### Reverse Chaining
```
GET /Patient?_has:Observation:subject:code=http://loinc.org|55284-4
GET /Patient?_has:Condition:subject:category=problem-list-item
```

## Search Implementation Patterns

### Search Parameter Processing
```python
def process_search_params(resource_type: str, params: dict) -> dict:
    """Convert FHIR search parameters to database query"""
    query = {}
    
    for param_name, values in params.items():
        # Handle modifiers
        base_param, modifier = parse_modifier(param_name)
        
        # Get parameter definition
        search_param = get_search_parameter(resource_type, base_param)
        if not search_param:
            continue
            
        # Process based on parameter type
        if search_param['type'] == 'string':
            query[base_param] = process_string_search(values, modifier)
        elif search_param['type'] == 'token':
            query[base_param] = process_token_search(values, modifier)
        elif search_param['type'] == 'date':
            query[base_param] = process_date_search(values, modifier)
        # ... other types
            
    return query
```

### Bundle Search Results
```python
def create_search_bundle(resources: list, total: int, params: dict) -> dict:
    """Create FHIR Bundle for search results"""
    return {
        'resourceType': 'Bundle',
        'type': 'searchset',
        'total': total,
        'link': [
            {
                'relation': 'self',
                'url': build_search_url(params)
            },
            # Add next/prev links for pagination
        ],
        'entry': [
            {
                'resource': resource,
                'search': {'mode': 'match'}
            } for resource in resources
        ]
    }
```

### Compartment-based Search
```python
# Patient compartment search
GET /Patient/123/Observation  # All observations for patient 123
GET /Patient/123/DiagnosticReport
GET /Patient/123/*  # All resources in patient compartment

def get_compartment_resources(compartment_type: str, id: str, resource_type: str = None):
    """Get resources within a compartment"""
    if compartment_type == 'Patient':
        return get_patient_compartment_resources(id, resource_type)
    elif compartment_type == 'Encounter':
        return get_encounter_compartment_resources(id, resource_type)
    # ... other compartments
```

## Error Handling

### Invalid Search Parameters
```json
{
  "resourceType": "OperationOutcome",
  "issue": [{
    "severity": "error",
    "code": "invalid",
    "details": {
      "text": "Unknown search parameter: invalidParam"
    },
    "location": ["invalidParam"]
  }]
}
```

### Search Parameter Validation
```python
def validate_search_parameters(resource_type: str, params: dict) -> list:
    """Validate search parameters and return issues"""
    issues = []
    
    for param_name in params:
        base_param, modifier = parse_modifier(param_name)
        
        # Check if parameter exists
        if not search_parameter_exists(resource_type, base_param):
            issues.append({
                'severity': 'error',
                'code': 'not-supported',
                'details': {'text': f'Unknown search parameter: {base_param}'},
                'location': [param_name]
            })
        
        # Validate modifier
        if modifier and not modifier_supported(base_param, modifier):
            issues.append({
                'severity': 'error', 
                'code': 'not-supported',
                'details': {'text': f'Unsupported modifier: {modifier}'},
                'location': [param_name]
            })
    
    return issues
```

## Performance Optimization

### Indexed Search Parameters
```sql
-- Database indexes for common FHIR searches
CREATE INDEX idx_patient_family ON patient_names(family);
CREATE INDEX idx_patient_given ON patient_names(given);
CREATE INDEX idx_patient_birthdate ON patients(birth_date);
CREATE INDEX idx_observation_code ON observations(code_system, code_value);
CREATE INDEX idx_observation_subject ON observations(subject_reference);
CREATE INDEX idx_observation_date ON observations(effective_datetime);
```

### Search Parameter Caching
```python
@lru_cache(maxsize=1000)
def get_search_parameter(resource_type: str, param_name: str) -> dict:
    """Cache search parameter definitions"""
    return load_search_parameter_from_spec(resource_type, param_name)
```

### Batch Search Processing
```python
async def batch_search(searches: list) -> dict:
    """Process multiple searches in a batch"""
    results = {}
    
    # Group searches by resource type for optimization
    grouped = group_searches_by_type(searches)
    
    for resource_type, type_searches in grouped.items():
        type_results = await process_resource_searches(resource_type, type_searches)
        results.update(type_results)
    
    return results
```

## Testing Search Implementation

### Search Parameter Tests
```python
def test_string_search():
    # Test basic string search
    result = search_patients({'name': 'john'})
    assert any('john' in name.lower() for patient in result for name in patient.get_names())
    
    # Test exact modifier
    result = search_patients({'name:exact': 'John'})
    assert all('John' in patient.get_display_names() for patient in result)

def test_token_search():
    # Test system|code format
    result = search_observations({'code': 'http://loinc.org|55284-4'})
    assert all(obs.code.system == 'http://loinc.org' and obs.code.code == '55284-4' 
              for obs in result)

def test_date_search():
    # Test date range
    result = search_patients({'birthdate': 'ge1990-01-01&birthdate=lt2000-01-01'})
    assert all(1990 <= get_birth_year(patient) < 2000 for patient in result)
```

## Integration with FHIR Servers

### Popular FHIR Server Search APIs

**HAPI FHIR:**
- Full SearchParameter support
- Custom search parameter definitions
- Subscription support

**Microsoft FHIR Server:**
- Core search parameters
- Custom search parameters via SearchParameter resources
- Azure-optimized queries

**Google FHIR Store:**
- Standard FHIR search
- BigQuery integration for analytics
- Custom search with views

**AWS HealthLake:**
- FHIR R4 search support
- Natural language query (NLQ)
- Integrated analytics
