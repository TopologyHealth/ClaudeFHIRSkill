#!/usr/bin/env python3
"""
Basic FHIR Server using FastAPI
Provides a foundation for building FHIR-compliant APIs
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
import uvicorn
from datetime import datetime
import json
import os

# FHIR imports
from fhir.resources.patient import Patient
from fhir.resources.observation import Observation
from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.capabilitystatement import CapabilityStatement
from fhir.resources.operationoutcome import OperationOutcome, OperationOutcomeIssue
from pydantic import ValidationError

app = FastAPI(
    title="Example FHIR Server",
    description="Basic FHIR R4 compliant server",
    version="1.0.0",
    docs_url="/docs"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (use a real database in production)
patients_db: Dict[str, Dict] = {}
observations_db: Dict[str, Dict] = {}

# Utility functions
def create_operation_outcome(severity: str, code: str, details: str) -> Dict:
    """Create FHIR OperationOutcome for error responses"""
    issue = OperationOutcomeIssue(
        severity=severity,
        code=code,
        details={"text": details}
    )
    outcome = OperationOutcome(issue=[issue])
    return outcome.dict(exclude_none=True)

def generate_id() -> str:
    """Generate a simple ID for resources"""
    from uuid import uuid4
    return str(uuid4())

def validate_fhir_resource(resource_data: Dict, resource_class) -> Any:
    """Validate FHIR resource using Pydantic models"""
    try:
        return resource_class(**resource_data)
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=create_operation_outcome("error", "invalid", str(e))
        )

# Dependency for FHIR content type
async def validate_fhir_content_type(request: Request):
    content_type = request.headers.get("content-type", "")
    if request.method in ["POST", "PUT"] and "application/fhir+json" not in content_type:
        if "application/json" not in content_type:
            raise HTTPException(
                status_code=415,
                detail=create_operation_outcome(
                    "error", "not-supported", 
                    "Content-Type must be application/fhir+json or application/json"
                )
            )

# Metadata endpoint
@app.get("/metadata", response_model=Dict)
async def get_capability_statement():
    """Return server capability statement"""
    capability = {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": datetime.utcnow().isoformat() + "Z",
        "publisher": "Example FHIR Server",
        "kind": "instance",
        "software": {
            "name": "FastAPI FHIR Server",
            "version": "1.0.0"
        },
        "fhirVersion": "4.0.1",
        "format": ["application/fhir+json"],
        "rest": [{
            "mode": "server",
            "resource": [
                {
                    "type": "Patient",
                    "interaction": [
                        {"code": "read"},
                        {"code": "create"},
                        {"code": "update"},
                        {"code": "delete"},
                        {"code": "search-type"}
                    ],
                    "searchParam": [
                        {"name": "name", "type": "string"},
                        {"name": "family", "type": "string"},
                        {"name": "given", "type": "string"},
                        {"name": "birthdate", "type": "date"},
                        {"name": "gender", "type": "token"}
                    ]
                },
                {
                    "type": "Observation", 
                    "interaction": [
                        {"code": "read"},
                        {"code": "create"},
                        {"code": "search-type"}
                    ],
                    "searchParam": [
                        {"name": "subject", "type": "reference"},
                        {"name": "patient", "type": "reference"},
                        {"name": "code", "type": "token"},
                        {"name": "date", "type": "date"}
                    ]
                }
            ]
        }]
    }
    return capability

# Patient endpoints
@app.post("/Patient", dependencies=[Depends(validate_fhir_content_type)])
async def create_patient(patient_data: Dict[str, Any]):
    """Create a new patient"""
    patient = validate_fhir_resource(patient_data, Patient)
    
    # Generate ID if not provided
    if not patient.id:
        patient.id = generate_id()
    
    # Add metadata
    patient.meta = {
        "versionId": "1",
        "lastUpdated": datetime.utcnow().isoformat() + "Z"
    }
    
    # Store in database
    patients_db[patient.id] = patient.dict(exclude_none=True)
    
    return JSONResponse(
        status_code=201,
        content=patients_db[patient.id],
        headers={"Location": f"/Patient/{patient.id}"}
    )

@app.get("/Patient/{patient_id}")
async def get_patient(patient_id: str):
    """Read a patient by ID"""
    if patient_id not in patients_db:
        raise HTTPException(
            status_code=404,
            detail=create_operation_outcome("error", "not-found", f"Patient/{patient_id} not found")
        )
    
    return patients_db[patient_id]

@app.put("/Patient/{patient_id}", dependencies=[Depends(validate_fhir_content_type)])
async def update_patient(patient_id: str, patient_data: Dict[str, Any]):
    """Update an existing patient"""
    patient = validate_fhir_resource(patient_data, Patient)
    
    # Ensure ID matches URL
    patient.id = patient_id
    
    # Update metadata
    existing = patients_db.get(patient_id, {})
    current_version = int(existing.get("meta", {}).get("versionId", "0"))
    
    patient.meta = {
        "versionId": str(current_version + 1),
        "lastUpdated": datetime.utcnow().isoformat() + "Z"
    }
    
    # Store in database
    patients_db[patient_id] = patient.dict(exclude_none=True)
    
    return patients_db[patient_id]

@app.delete("/Patient/{patient_id}")
async def delete_patient(patient_id: str):
    """Delete a patient"""
    if patient_id not in patients_db:
        raise HTTPException(
            status_code=404,
            detail=create_operation_outcome("error", "not-found", f"Patient/{patient_id} not found")
        )
    
    del patients_db[patient_id]
    
    return JSONResponse(status_code=204, content=None)

@app.get("/Patient")
async def search_patients(
    name: Optional[str] = None,
    family: Optional[str] = None, 
    given: Optional[str] = None,
    birthdate: Optional[str] = None,
    gender: Optional[str] = None,
    _count: Optional[int] = 20,
    _offset: Optional[int] = 0
):
    """Search for patients"""
    results = []
    
    for patient_data in patients_db.values():
        match = True
        
        # Simple string matching for name fields
        if name and patient_data.get("name"):
            name_match = any(
                name.lower() in (n.get("family", "") + " " + " ".join(n.get("given", []))).lower()
                for n in patient_data["name"]
            )
            if not name_match:
                match = False
        
        if family and patient_data.get("name"):
            family_match = any(
                family.lower() in n.get("family", "").lower()
                for n in patient_data["name"]
            )
            if not family_match:
                match = False
        
        if given and patient_data.get("name"):
            given_match = any(
                any(given.lower() in g.lower() for g in n.get("given", []))
                for n in patient_data["name"]
            )
            if not given_match:
                match = False
        
        if birthdate and patient_data.get("birthDate") != birthdate:
            match = False
            
        if gender and patient_data.get("gender") != gender:
            match = False
        
        if match:
            results.append(patient_data)
    
    # Apply pagination
    total = len(results)
    paginated_results = results[_offset:_offset + _count]
    
    # Create Bundle
    bundle = {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": total,
        "entry": [
            {
                "resource": result,
                "search": {"mode": "match"}
            }
            for result in paginated_results
        ]
    }
    
    return bundle

# Observation endpoints
@app.post("/Observation", dependencies=[Depends(validate_fhir_content_type)])
async def create_observation(observation_data: Dict[str, Any]):
    """Create a new observation"""
    observation = validate_fhir_resource(observation_data, Observation)
    
    if not observation.id:
        observation.id = generate_id()
    
    observation.meta = {
        "versionId": "1",
        "lastUpdated": datetime.utcnow().isoformat() + "Z"
    }
    
    observations_db[observation.id] = observation.dict(exclude_none=True)
    
    return JSONResponse(
        status_code=201,
        content=observations_db[observation.id],
        headers={"Location": f"/Observation/{observation.id}"}
    )

@app.get("/Observation/{observation_id}")
async def get_observation(observation_id: str):
    """Read an observation by ID"""
    if observation_id not in observations_db:
        raise HTTPException(
            status_code=404,
            detail=create_operation_outcome("error", "not-found", f"Observation/{observation_id} not found")
        )
    
    return observations_db[observation_id]

@app.get("/Observation")
async def search_observations(
    subject: Optional[str] = None,
    patient: Optional[str] = None,
    code: Optional[str] = None,
    date: Optional[str] = None,
    _count: Optional[int] = 20
):
    """Search for observations"""
    results = []
    
    for obs_data in observations_db.values():
        match = True
        
        # Subject/patient reference matching
        if subject and obs_data.get("subject", {}).get("reference") != subject:
            match = False
        
        if patient and obs_data.get("subject", {}).get("reference") != f"Patient/{patient}":
            match = False
        
        # Simple code matching
        if code and obs_data.get("code"):
            code_match = any(
                code in coding.get("code", "")
                for coding in obs_data["code"].get("coding", [])
            )
            if not code_match:
                match = False
        
        # Date matching (simplified)
        if date:
            obs_date = obs_data.get("effectiveDateTime", "")
            if not obs_date.startswith(date):
                match = False
        
        if match:
            results.append(obs_data)
    
    bundle = {
        "resourceType": "Bundle",
        "type": "searchset", 
        "total": len(results),
        "entry": [
            {
                "resource": result,
                "search": {"mode": "match"}
            }
            for result in results[:_count]
        ]
    }
    
    return bundle

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
