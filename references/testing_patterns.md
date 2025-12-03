# FHIR Testing and Quality Assurance Reference

This document provides comprehensive guidance for testing FHIR implementations, including unit tests, integration tests, validation tests, and performance testing.

## Unit Testing FHIR Resources

### Resource Validation Tests
```python
import pytest
from fhir.resources.patient import Patient
from fhir.resources.observation import Observation
from pydantic import ValidationError
import json

class TestFHIRResources:
    def test_valid_patient_creation(self):
        """Test creating a valid patient resource"""
        patient_data = {
            "resourceType": "Patient",
            "id": "test-patient",
            "active": True,
            "name": [
                {
                    "family": "Doe",
                    "given": ["John", "Michael"]
                }
            ],
            "gender": "male",
            "birthDate": "1990-01-01"
        }
        
        patient = Patient(**patient_data)
        assert patient.resourceType == "Patient"
        assert patient.id == "test-patient"
        assert patient.active is True
        assert len(patient.name) == 1
        assert patient.name[0].family == "Doe"
        assert patient.gender == "male"
    
    def test_invalid_patient_gender(self):
        """Test patient with invalid gender value"""
        patient_data = {
            "resourceType": "Patient",
            "gender": "invalid-gender"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            Patient(**patient_data)
        
        assert "gender" in str(exc_info.value)
    
    def test_patient_serialization(self):
        """Test patient serialization to JSON"""
        patient = Patient(
            resourceType="Patient",
            id="test-patient",
            active=True,
            name=[{"family": "Doe", "given": ["John"]}],
            gender="male"
        )
        
        json_data = patient.json(exclude_none=True)
        parsed_data = json.loads(json_data)
        
        assert parsed_data["resourceType"] == "Patient"
        assert parsed_data["id"] == "test-patient"
        assert parsed_data["active"] is True
    
    def test_observation_with_quantity_value(self):
        """Test observation with quantity value"""
        obs_data = {
            "resourceType": "Observation",
            "status": "final",
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "55284-4",
                    "display": "Blood pressure"
                }]
            },
            "subject": {"reference": "Patient/123"},
            "valueQuantity": {
                "value": 120,
                "unit": "mmHg",
                "system": "http://unitsofmeasure.org",
                "code": "mm[Hg]"
            }
        }
        
        observation = Observation(**obs_data)
        assert observation.status == "final"
        assert observation.valueQuantity.value == 120
        assert observation.valueQuantity.unit == "mmHg"
    
    def test_observation_missing_required_fields(self):
        """Test observation missing required fields"""
        obs_data = {
            "resourceType": "Observation"
            # Missing status, code, subject
        }
        
        with pytest.raises(ValidationError) as exc_info:
            Observation(**obs_data)
        
        error_msg = str(exc_info.value)
        assert "status" in error_msg
        assert "code" in error_msg

@pytest.fixture
def sample_patient():
    """Fixture providing a sample patient"""
    return Patient(
        resourceType="Patient",
        id="sample-patient",
        active=True,
        name=[{
            "family": "Smith", 
            "given": ["Jane"]
        }],
        gender="female",
        birthDate="1985-03-15"
    )

def test_patient_fixture(sample_patient):
    """Test using patient fixture"""
    assert sample_patient.name[0].family == "Smith"
    assert sample_patient.gender == "female"
```

## API Integration Tests

### FHIR Server Testing
```python
import pytest
import httpx
import asyncio
from typing import AsyncGenerator

@pytest.fixture
async def test_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Async test client for FHIR server"""
    async with httpx.AsyncClient(
        base_url="http://localhost:8000",
        timeout=30.0
    ) as client:
        yield client

@pytest.fixture
def patient_data():
    """Sample patient data for testing"""
    return {
        "resourceType": "Patient",
        "active": True,
        "name": [{
            "family": "TestPatient",
            "given": ["Integration"]
        }],
        "gender": "unknown",
        "birthDate": "1990-01-01"
    }

class TestFHIRServerAPI:
    
    @pytest.mark.asyncio
    async def test_server_metadata(self, test_client):
        """Test capability statement endpoint"""
        response = await test_client.get("/metadata")
        assert response.status_code == 200
        
        data = response.json()
        assert data["resourceType"] == "CapabilityStatement"
        assert data["fhirVersion"] == "4.0.1"
        assert "rest" in data
        
        # Check supported resources
        resources = data["rest"][0]["resource"]
        resource_types = [r["type"] for r in resources]
        assert "Patient" in resource_types
        assert "Observation" in resource_types
    
    @pytest.mark.asyncio
    async def test_patient_crud_operations(self, test_client, patient_data):
        """Test complete patient CRUD cycle"""
        
        # CREATE
        create_response = await test_client.post(
            "/Patient",
            json=patient_data,
            headers={"Content-Type": "application/fhir+json"}
        )
        assert create_response.status_code == 201
        
        created_patient = create_response.json()
        patient_id = created_patient["id"]
        assert created_patient["resourceType"] == "Patient"
        assert "meta" in created_patient
        
        # READ
        read_response = await test_client.get(f"/Patient/{patient_id}")
        assert read_response.status_code == 200
        
        read_patient = read_response.json()
        assert read_patient["id"] == patient_id
        assert read_patient["name"][0]["family"] == "TestPatient"
        
        # UPDATE
        read_patient["active"] = False
        update_response = await test_client.put(
            f"/Patient/{patient_id}",
            json=read_patient,
            headers={"Content-Type": "application/fhir+json"}
        )
        assert update_response.status_code == 200
        
        updated_patient = update_response.json()
        assert updated_patient["active"] is False
        assert int(updated_patient["meta"]["versionId"]) > int(created_patient["meta"]["versionId"])
        
        # DELETE
        delete_response = await test_client.delete(f"/Patient/{patient_id}")
        assert delete_response.status_code == 204
        
        # Verify deletion
        get_deleted_response = await test_client.get(f"/Patient/{patient_id}")
        assert get_deleted_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_patient_search(self, test_client):
        """Test patient search functionality"""
        
        # Create test patients
        patients = [
            {
                "resourceType": "Patient",
                "name": [{"family": "Smith", "given": ["John"]}],
                "gender": "male",
                "birthDate": "1980-01-01"
            },
            {
                "resourceType": "Patient", 
                "name": [{"family": "Smith", "given": ["Jane"]}],
                "gender": "female",
                "birthDate": "1985-05-15"
            },
            {
                "resourceType": "Patient",
                "name": [{"family": "Doe", "given": ["Bob"]}],
                "gender": "male",
                "birthDate": "1990-12-25"
            }
        ]
        
        created_ids = []
        for patient_data in patients:
            response = await test_client.post(
                "/Patient",
                json=patient_data,
                headers={"Content-Type": "application/fhir+json"}
            )
            assert response.status_code == 201
            created_ids.append(response.json()["id"])
        
        try:
            # Search by family name
            search_response = await test_client.get("/Patient?family=Smith")
            assert search_response.status_code == 200
            
            search_results = search_response.json()
            assert search_results["resourceType"] == "Bundle"
            assert search_results["total"] == 2
            
            # Search by gender
            search_response = await test_client.get("/Patient?gender=male")
            assert search_response.status_code == 200
            
            search_results = search_response.json()
            assert search_results["total"] == 2
            
            # Search by birth date
            search_response = await test_client.get("/Patient?birthdate=1980-01-01")
            assert search_response.status_code == 200
            
            search_results = search_response.json()
            assert search_results["total"] == 1
            assert search_results["entry"][0]["resource"]["name"][0]["given"][0] == "John"
        
        finally:
            # Cleanup
            for patient_id in created_ids:
                await test_client.delete(f"/Patient/{patient_id}")
    
    @pytest.mark.asyncio
    async def test_invalid_resource_handling(self, test_client):
        """Test error handling for invalid resources"""
        
        # Invalid resource type
        invalid_data = {
            "resourceType": "InvalidResource",
            "someField": "someValue"
        }
        
        response = await test_client.post(
            "/Patient",
            json=invalid_data,
            headers={"Content-Type": "application/fhir+json"}
        )
        assert response.status_code == 400
        
        error_response = response.json()
        assert "OperationOutcome" in str(error_response) or "detail" in error_response
    
    @pytest.mark.asyncio
    async def test_content_type_validation(self, test_client, patient_data):
        """Test content type validation"""
        
        # Missing content type
        response = await test_client.post("/Patient", json=patient_data)
        # Should accept application/json as fallback
        assert response.status_code in [201, 415]  # Depends on implementation
        
        # Correct FHIR content type
        response = await test_client.post(
            "/Patient",
            json=patient_data,
            headers={"Content-Type": "application/fhir+json"}
        )
        assert response.status_code == 201
```

## Validation Testing

### Profile Validation Tests
```python
import pytest
from unittest.mock import Mock, patch
from fhir_validator import FHIRValidator, StructureDefinitionLoader

class TestFHIRValidation:
    
    @pytest.fixture
    def validator(self):
        """Create validator with mock package manager"""
        mock_package_manager = Mock()
        return FHIRValidator(mock_package_manager)
    
    @pytest.fixture
    def us_core_patient_profile(self):
        """Mock US Core Patient profile"""
        return {
            "resourceType": "StructureDefinition",
            "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient",
            "differential": {
                "element": [
                    {
                        "path": "Patient.identifier",
                        "min": 1,
                        "mustSupport": True
                    },
                    {
                        "path": "Patient.name",
                        "min": 1,
                        "mustSupport": True
                    }
                ]
            }
        }
    
    def test_valid_us_core_patient(self, validator):
        """Test validation against US Core Patient profile"""
        patient_data = {
            "resourceType": "Patient",
            "id": "example",
            "meta": {
                "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"]
            },
            "identifier": [{
                "system": "http://hospital.org/patients",
                "value": "123456"
            }],
            "name": [{
                "family": "Doe",
                "given": ["John"]
            }],
            "gender": "male"
        }
        
        with patch.object(
            validator.structure_loader, 
            'load_structure_definition',
            return_value=us_core_patient_profile()
        ):
            result = validator.validate_resource(
                patient_data,
                ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"]
            )
            
            assert result.valid
            assert len(result.errors) == 0
    
    def test_invalid_us_core_patient_missing_identifier(self, validator, us_core_patient_profile):
        """Test US Core Patient missing required identifier"""
        patient_data = {
            "resourceType": "Patient",
            "name": [{
                "family": "Doe", 
                "given": ["John"]
            }]
        }
        
        with patch.object(
            validator.structure_loader,
            'load_structure_definition', 
            return_value=us_core_patient_profile
        ):
            result = validator.validate_resource(
                patient_data,
                ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"]
            )
            
            assert not result.valid
            assert any("identifier" in error.lower() for error in result.errors)
    
    def test_terminology_validation(self, validator):
        """Test validation of coded values against ValueSets"""
        observation_data = {
            "resourceType": "Observation",
            "status": "final",
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "55284-4",
                    "display": "Blood pressure"
                }]
            },
            "subject": {"reference": "Patient/123"},
            "valueQuantity": {
                "value": 120,
                "unit": "mmHg",
                "system": "http://unitsofmeasure.org",
                "code": "mm[Hg]"
            }
        }
        
        # Mock terminology validation
        with patch.object(
            validator.terminology_validator,
            'validate_coding',
            return_value=[]
        ):
            result = validator.validate_resource(observation_data)
            assert result.valid
```

## Performance Testing

### Load Testing with Locust
```python
from locust import HttpUser, task, between
import json
import random

class FHIRServerUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Setup test data"""
        self.patient_ids = []
        self.observation_ids = []
        
        # Create some test patients
        for i in range(5):
            patient_data = {
                "resourceType": "Patient",
                "name": [{
                    "family": f"TestFamily{i}",
                    "given": [f"TestGiven{i}"]
                }],
                "gender": random.choice(["male", "female"]),
                "birthDate": f"198{i}-01-01"
            }
            
            response = self.client.post(
                "/Patient",
                json=patient_data,
                headers={"Content-Type": "application/fhir+json"}
            )
            
            if response.status_code == 201:
                self.patient_ids.append(response.json()["id"])
    
    @task(3)
    def search_patients(self):
        """Search for patients (most common operation)"""
        search_params = [
            "?family=Test",
            "?gender=male",
            "?birthdate=ge1980",
            "?_count=10"
        ]
        
        param = random.choice(search_params)
        self.client.get(f"/Patient{param}")
    
    @task(2)
    def read_patient(self):
        """Read specific patient"""
        if self.patient_ids:
            patient_id = random.choice(self.patient_ids)
            self.client.get(f"/Patient/{patient_id}")
    
    @task(1)
    def create_observation(self):
        """Create observation for existing patient"""
        if self.patient_ids:
            patient_id = random.choice(self.patient_ids)
            
            observation_data = {
                "resourceType": "Observation",
                "status": "final",
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "55284-4",
                        "display": "Blood pressure"
                    }]
                },
                "subject": {"reference": f"Patient/{patient_id}"},
                "valueQuantity": {
                    "value": random.randint(90, 180),
                    "unit": "mmHg",
                    "system": "http://unitsofmeasure.org",
                    "code": "mm[Hg]"
                }
            }
            
            response = self.client.post(
                "/Observation",
                json=observation_data,
                headers={"Content-Type": "application/fhir+json"}
            )
            
            if response.status_code == 201:
                self.observation_ids.append(response.json()["id"])
    
    @task(1)
    def get_server_metadata(self):
        """Get server capability statement"""
        self.client.get("/metadata")
```

## Conformance Testing

### FHIR Test Suite Integration
```python
import pytest
import json
import requests
from pathlib import Path

class TestFHIRConformance:
    """Test suite for FHIR conformance testing"""
    
    @pytest.fixture(scope="class")
    def test_server_url(self):
        """FHIR server URL for testing"""
        return "http://localhost:8000"
    
    @pytest.fixture(scope="class")
    def capability_statement(self, test_server_url):
        """Get server capability statement"""
        response = requests.get(f"{test_server_url}/metadata")
        assert response.status_code == 200
        return response.json()
    
    def test_capability_statement_structure(self, capability_statement):
        """Test capability statement has required fields"""
        assert capability_statement["resourceType"] == "CapabilityStatement"
        assert "fhirVersion" in capability_statement
        assert "rest" in capability_statement
        assert len(capability_statement["rest"]) > 0
        
        rest = capability_statement["rest"][0]
        assert rest["mode"] == "server"
        assert "resource" in rest
    
    def test_supported_resources(self, capability_statement):
        """Test server supports required resource types"""
        rest = capability_statement["rest"][0]
        supported_types = [r["type"] for r in rest["resource"]]
        
        # Check minimum required resources
        required_resources = ["Patient", "Observation"]
        for resource_type in required_resources:
            assert resource_type in supported_types
    
    def test_search_parameters(self, capability_statement):
        """Test search parameters are properly defined"""
        rest = capability_statement["rest"][0]
        
        for resource in rest["resource"]:
            if resource["type"] == "Patient":
                search_params = {p["name"]: p["type"] for p in resource.get("searchParam", [])}
                
                # Check required Patient search parameters
                assert "name" in search_params
                assert "family" in search_params
                assert "birthdate" in search_params
                
                # Verify parameter types
                assert search_params["name"] == "string"
                assert search_params["birthdate"] == "date"
    
    @pytest.mark.parametrize("format_type", [
        "application/fhir+json",
        "application/json",
        "application/fhir+xml"  # If supported
    ])
    def test_supported_formats(self, test_server_url, capability_statement, format_type):
        """Test server supports advertised formats"""
        supported_formats = capability_statement.get("format", [])
        
        if format_type in supported_formats:
            headers = {"Accept": format_type}
            response = requests.get(f"{test_server_url}/metadata", headers=headers)
            assert response.status_code == 200
            
            if "json" in format_type:
                # Should be valid JSON
                response.json()
            elif "xml" in format_type:
                # Should be valid XML (basic check)
                assert response.text.startswith("<?xml") or response.text.startswith("<")

def test_fhir_examples_validation():
    """Test validation of official FHIR examples"""
    examples_dir = Path("test_data/fhir_examples")
    
    if not examples_dir.exists():
        pytest.skip("FHIR examples directory not found")
    
    validator = FHIRValidator(None)  # Mock package manager
    
    for example_file in examples_dir.glob("*.json"):
        with open(example_file) as f:
            resource_data = json.load(f)
        
        # Basic validation
        result = validator.validate_resource(resource_data)
        
        if not result.valid:
            pytest.fail(
                f"Official example {example_file.name} failed validation: "
                f"{', '.join(result.errors)}"
            )

class TestInteroperability:
    """Test interoperability with other FHIR servers"""
    
    @pytest.mark.parametrize("server_url", [
        "https://hapi.fhir.org/baseR4",
        "https://launch.smarthealthit.org/v/r4/fhir",
        # Add other test servers
    ])
    def test_cross_server_patient_read(self, server_url):
        """Test reading patients from different FHIR servers"""
        try:
            # Try to read a known test patient
            response = requests.get(
                f"{server_url}/Patient",
                headers={"Accept": "application/fhir+json"},
                timeout=10
            )
            
            if response.status_code == 200:
                bundle = response.json()
                assert bundle["resourceType"] == "Bundle"
                
                # Validate first patient if available
                if bundle.get("entry"):
                    patient = bundle["entry"][0]["resource"]
                    assert patient["resourceType"] == "Patient"
        
        except requests.RequestException:
            pytest.skip(f"Server {server_url} not accessible")
```

## Test Data Management

### Test Data Factory
```python
import factory
from faker import Faker
from datetime import datetime, timedelta
import random

fake = Faker()

class PatientFactory(factory.Factory):
    """Factory for generating test Patient resources"""
    
    class Meta:
        model = dict
    
    resourceType = "Patient"
    id = factory.LazyAttribute(lambda obj: fake.uuid4())
    active = True
    
    @factory.LazyAttribute
    def name(obj):
        return [{
            "family": fake.last_name(),
            "given": [fake.first_name(), fake.first_name()]
        }]
    
    gender = factory.LazyAttribute(
        lambda obj: random.choice(["male", "female", "other", "unknown"])
    )
    
    @factory.LazyAttribute
    def birthDate(obj):
        birth_date = fake.date_between(start_date="-80y", end_date="-18y")
        return birth_date.isoformat()
    
    @factory.LazyAttribute
    def identifier(obj):
        return [{
            "system": "http://hospital.org/patients",
            "value": fake.random_number(digits=8)
        }]

class ObservationFactory(factory.Factory):
    """Factory for generating test Observation resources"""
    
    class Meta:
        model = dict
    
    resourceType = "Observation"
    id = factory.LazyAttribute(lambda obj: fake.uuid4())
    status = "final"
    
    @factory.LazyAttribute
    def code(obj):
        return {
            "coding": [{
                "system": "http://loinc.org",
                "code": random.choice(["55284-4", "8480-6", "8462-4"]),
                "display": random.choice(["Blood pressure", "Systolic BP", "Diastolic BP"])
            }]
        }
    
    @factory.LazyAttribute
    def subject(obj):
        return {"reference": f"Patient/{fake.uuid4()}"}
    
    @factory.LazyAttribute
    def effectiveDateTime(obj):
        effect_time = fake.date_time_between(start_date="-1y", end_date="now")
        return effect_time.isoformat()
    
    @factory.LazyAttribute
    def valueQuantity(obj):
        return {
            "value": random.randint(80, 180),
            "unit": "mmHg",
            "system": "http://unitsofmeasure.org",
            "code": "mm[Hg]"
        }

# Usage examples
def test_with_factory_data():
    """Test using factory-generated data"""
    patient = PatientFactory()
    observation = ObservationFactory(subject={"reference": f"Patient/{patient['id']}"})
    
    assert patient["resourceType"] == "Patient"
    assert observation["subject"]["reference"].startswith("Patient/")
    
    # Create multiple resources
    patients = PatientFactory.create_batch(10)
    assert len(patients) == 10
```

## Continuous Integration

### GitHub Actions FHIR Testing
```yaml
# .github/workflows/fhir-tests.yml
name: FHIR Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: fhir_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Install FHIR packages
      run: |
        python scripts/fhir_package_manager.py install hl7.fhir.r4.core 4.0.1
        python scripts/fhir_package_manager.py install hl7.fhir.us.core 5.0.1
    
    - name: Run FHIR validation tests
      run: |
        python scripts/fhir_validator.py validate test_data/patient_example.json
        python scripts/fhir_validator.py validate test_data/observation_example.json
    
    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=src
    
    - name: Start FHIR server
      run: |
        python src/fhir_server.py &
        sleep 5
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/fhir_test
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v
    
    - name: Run conformance tests
      run: |
        pytest tests/conformance/ -v
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
```

This comprehensive testing reference provides patterns for ensuring FHIR implementation quality across all testing levels, from unit tests to full conformance testing.
