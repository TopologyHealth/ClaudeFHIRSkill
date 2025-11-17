# FHIR Validation and StructureDefinition Reference

This document provides comprehensive guidance on FHIR resource validation, profile validation, and working with StructureDefinitions.

## Validation Levels

### 1. Structure Validation
Validates basic FHIR structure and data types.

```python
def validate_fhir_structure(resource: dict) -> ValidationResult:
    """Validate basic FHIR resource structure"""
    errors = []
    warnings = []
    
    # Required fields
    if not resource.get('resourceType'):
        errors.append("Missing required field: resourceType")
    
    # ID validation
    if 'id' in resource:
        if not re.match(r'^[A-Za-z0-9\-\.]{1,64}$', resource['id']):
            errors.append("Invalid id format")
    
    # Meta validation
    if 'meta' in resource:
        meta = resource['meta']
        if 'versionId' in meta and not re.match(r'^[A-Za-z0-9\-\.]{1,64}$', meta['versionId']):
            errors.append("Invalid meta.versionId format")
    
    return ValidationResult(len(errors) == 0, errors, warnings)
```

### 2. Data Type Validation
Validates FHIR primitive and complex data types.

```python
from datetime import datetime
import re

def validate_fhir_datatypes(element: any, element_type: str) -> list:
    """Validate FHIR data types"""
    errors = []
    
    if element_type == 'date':
        if not re.match(r'^\d{4}(-\d{2}(-\d{2})?)?$', str(element)):
            errors.append(f"Invalid date format: {element}")
    
    elif element_type == 'dateTime':
        try:
            # FHIR dateTime format: YYYY-MM-DDTHH:mm:ss+zz:zz
            datetime.fromisoformat(str(element).replace('Z', '+00:00'))
        except ValueError:
            errors.append(f"Invalid dateTime format: {element}")
    
    elif element_type == 'boolean':
        if element not in [True, False]:
            errors.append(f"Invalid boolean value: {element}")
    
    elif element_type == 'integer':
        if not isinstance(element, int) or element < -2147483648 or element > 2147483647:
            errors.append(f"Invalid integer value: {element}")
    
    elif element_type == 'decimal':
        if not isinstance(element, (int, float)):
            errors.append(f"Invalid decimal value: {element}")
    
    elif element_type == 'uri':
        # Basic URI validation
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', str(element)):
            errors.append(f"Invalid URI format: {element}")
    
    elif element_type == 'url':
        # URL should be absolute
        if not re.match(r'^https?://', str(element)):
            errors.append(f"Invalid URL format: {element}")
    
    elif element_type == 'canonical':
        # Can be URL or URI
        if not (re.match(r'^https?://', str(element)) or 
                re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', str(element))):
            errors.append(f"Invalid canonical format: {element}")
    
    return errors
```

### 3. Cardinality Validation
Validates min/max occurrences of elements.

```python
def validate_cardinality(resource: dict, structure_def: dict) -> list:
    """Validate element cardinality against StructureDefinition"""
    errors = []
    
    for element in structure_def.get('differential', {}).get('element', []):
        path = element['path']
        min_occurs = element.get('min', 0)
        max_occurs = element.get('max', '*')
        
        # Extract value from resource using path
        values = extract_values_by_path(resource, path)
        value_count = len(values)
        
        # Check minimum cardinality
        if value_count < min_occurs:
            errors.append(f"{path}: minimum {min_occurs} occurrences required, found {value_count}")
        
        # Check maximum cardinality
        if max_occurs != '*' and value_count > int(max_occurs):
            errors.append(f"{path}: maximum {max_occurs} occurrences allowed, found {value_count}")
    
    return errors

def extract_values_by_path(resource: dict, fhir_path: str) -> list:
    """Extract values from resource using FHIRPath expression"""
    # Simplified implementation - real implementation would use FHIRPath evaluator
    parts = fhir_path.split('.')
    current = resource
    
    try:
        for part in parts[1:]:  # Skip resource type
            if '[' in part:
                # Handle array access like 'name[0]'
                field, index = part.split('[')
                index = int(index.rstrip(']'))
                current = current[field][index]
            else:
                current = current[part]
        
        return [current] if current is not None else []
    except (KeyError, IndexError, TypeError):
        return []
```

## Profile Validation

### Loading StructureDefinitions
```python
class StructureDefinitionLoader:
    def __init__(self, package_manager):
        self.package_manager = package_manager
        self.cache = {}
    
    def load_structure_definition(self, url: str) -> dict:
        """Load StructureDefinition by canonical URL"""
        if url in self.cache:
            return self.cache[url]
        
        # Search in loaded packages
        for package_id, version in self.get_loaded_packages():
            structure_defs = self.package_manager.search_resources(
                package_id, version, resource_type='StructureDefinition'
            )
            
            for sd in structure_defs:
                if sd.get('url') == url:
                    full_sd = self.load_resource_file(sd['file_path'])
                    self.cache[url] = full_sd
                    return full_sd
        
        raise ValueError(f"StructureDefinition not found: {url}")
    
    def get_loaded_packages(self) -> list:
        """Get list of loaded package IDs and versions"""
        return [
            ('hl7.fhir.r4.core', '4.0.1'),
            ('hl7.fhir.us.core', '5.0.1'),
            # Add other loaded packages
        ]
    
    def load_resource_file(self, file_path: str) -> dict:
        """Load FHIR resource from file"""
        with open(file_path, 'r') as f:
            return json.load(f)
```

### Profile-based Validation
```python
def validate_against_profile(resource: dict, profile_url: str, 
                           loader: StructureDefinitionLoader) -> ValidationResult:
    """Validate resource against specific profile"""
    errors = []
    warnings = []
    
    try:
        profile = loader.load_structure_definition(profile_url)
        
        # Validate must-support elements
        must_support_errors = validate_must_support(resource, profile)
        errors.extend(must_support_errors)
        
        # Validate constraints
        constraint_errors = validate_constraints(resource, profile)
        errors.extend(constraint_errors)
        
        # Validate cardinality
        cardinality_errors = validate_cardinality(resource, profile)
        errors.extend(cardinality_errors)
        
        # Validate fixed values
        fixed_value_errors = validate_fixed_values(resource, profile)
        errors.extend(fixed_value_errors)
        
        # Validate binding strengths
        binding_warnings = validate_value_set_bindings(resource, profile)
        warnings.extend(binding_warnings)
        
    except Exception as e:
        errors.append(f"Profile validation error: {str(e)}")
    
    return ValidationResult(len(errors) == 0, errors, warnings)

def validate_must_support(resource: dict, profile: dict) -> list:
    """Validate mustSupport elements are present"""
    errors = []
    
    for element in profile.get('differential', {}).get('element', []):
        if element.get('mustSupport'):
            path = element['path']
            values = extract_values_by_path(resource, path)
            
            if not values:
                errors.append(f"Missing mustSupport element: {path}")
    
    return errors

def validate_constraints(resource: dict, profile: dict) -> list:
    """Validate FHIRPath constraints"""
    errors = []
    
    for element in profile.get('differential', {}).get('element', []):
        for constraint in element.get('constraint', []):
            expression = constraint.get('expression')
            severity = constraint.get('severity', 'error')
            
            if expression:
                # Evaluate FHIRPath expression
                try:
                    result = evaluate_fhirpath(resource, expression)
                    if not result:
                        message = constraint.get('human', f"Constraint violation: {expression}")
                        if severity == 'error':
                            errors.append(f"{element['path']}: {message}")
                        # warnings would be handled similarly
                except Exception as e:
                    errors.append(f"Error evaluating constraint {constraint.get('key', '')}: {str(e)}")
    
    return errors
```

## ValueSet and CodeSystem Validation

### Terminology Validation
```python
class TerminologyValidator:
    def __init__(self, package_manager):
        self.package_manager = package_manager
        self.value_sets = {}
        self.code_systems = {}
    
    def validate_coding(self, coding: dict, binding: dict) -> list:
        """Validate Coding against ValueSet binding"""
        errors = []
        warnings = []
        
        if not coding:
            return errors
        
        value_set_url = binding.get('valueSet')
        strength = binding.get('strength', 'required')
        
        if not value_set_url:
            return errors
        
        try:
            value_set = self.load_value_set(value_set_url)
            is_valid = self.coding_in_value_set(coding, value_set)
            
            if not is_valid:
                message = f"Invalid code {coding.get('code')} from system {coding.get('system')}"
                
                if strength == 'required':
                    errors.append(message)
                elif strength in ['extensible', 'preferred']:
                    warnings.append(f"Recommended: {message}")
                # 'example' strength doesn't generate errors/warnings
        
        except Exception as e:
            errors.append(f"Terminology validation error: {str(e)}")
        
        return errors
    
    def load_value_set(self, url: str) -> dict:
        """Load ValueSet by URL"""
        if url in self.value_sets:
            return self.value_sets[url]
        
        # Search in packages
        for package_id, version in self.get_loaded_packages():
            value_sets = self.package_manager.search_resources(
                package_id, version, resource_type='ValueSet'
            )
            
            for vs in value_sets:
                if vs.get('url') == url:
                    full_vs = self.load_resource_file(vs['file_path'])
                    self.value_sets[url] = full_vs
                    return full_vs
        
        raise ValueError(f"ValueSet not found: {url}")
    
    def coding_in_value_set(self, coding: dict, value_set: dict) -> bool:
        """Check if Coding is in ValueSet"""
        system = coding.get('system')
        code = coding.get('code')
        
        if not system or not code:
            return False
        
        # Check expansion if present
        expansion = value_set.get('expansion')
        if expansion:
            for concept in expansion.get('contains', []):
                if (concept.get('system') == system and 
                    concept.get('code') == code):
                    return True
        
        # Check compose rules
        compose = value_set.get('compose')
        if compose:
            for include in compose.get('include', []):
                if self.coding_matches_include(coding, include):
                    return True
        
        return False
    
    def coding_matches_include(self, coding: dict, include: dict) -> bool:
        """Check if coding matches ValueSet include rules"""
        system = coding.get('system')
        code = coding.get('code')
        
        include_system = include.get('system')
        
        if include_system and include_system != system:
            return False
        
        # Check specific concepts
        concepts = include.get('concept', [])
        if concepts:
            return any(c.get('code') == code for c in concepts)
        
        # Check filters
        filters = include.get('filter', [])
        for filter_rule in filters:
            if not self.coding_matches_filter(coding, filter_rule):
                return False
        
        # If no specific concepts or filters, includes all codes from system
        return include_system == system
```

## Slicing Validation

### Slice Discrimination
```python
def validate_slicing(resource: dict, element_def: dict) -> list:
    """Validate array slicing rules"""
    errors = []
    path = element_def['path']
    slicing = element_def.get('slicing')
    
    if not slicing:
        return errors
    
    # Extract array values
    values = extract_values_by_path(resource, path)
    
    # Group values by discriminator
    discriminator = slicing['discriminator'][0]  # Simplified - handle multiple discriminators
    disc_type = discriminator['type']
    disc_path = discriminator['path']
    
    groups = {}
    for value in values:
        disc_value = extract_discriminator_value(value, disc_path, disc_type)
        if disc_value not in groups:
            groups[disc_value] = []
        groups[disc_value].append(value)
    
    # Validate slice cardinality
    slice_elements = get_slice_elements(element_def['path'])
    for slice_element in slice_elements:
        slice_name = get_slice_name(slice_element)
        expected_disc_value = get_slice_discriminator_value(slice_element)
        
        actual_count = len(groups.get(expected_disc_value, []))
        min_occurs = slice_element.get('min', 0)
        max_occurs = slice_element.get('max', '*')
        
        if actual_count < min_occurs:
            errors.append(f"Slice {slice_name}: minimum {min_occurs} required, found {actual_count}")
        
        if max_occurs != '*' and actual_count > int(max_occurs):
            errors.append(f"Slice {slice_name}: maximum {max_occurs} allowed, found {actual_count}")
    
    return errors

def extract_discriminator_value(element: dict, path: str, disc_type: str) -> str:
    """Extract discriminator value for slicing"""
    if disc_type == 'value':
        # Extract value at specified path
        return str(extract_values_by_path(element, path)[0] if 
                  extract_values_by_path(element, path) else '')
    
    elif disc_type == 'type':
        # Discriminate by element type
        return element.get('resourceType', type(element).__name__)
    
    elif disc_type == 'profile':
        # Discriminate by profile in meta
        profiles = element.get('meta', {}).get('profile', [])
        return profiles[0] if profiles else ''
    
    elif disc_type == 'pattern':
        # Complex pattern matching would go here
        pass
    
    return ''
```

## Extension Validation

### Extension Handling
```python
def validate_extensions(resource: dict, structure_def: dict) -> list:
    """Validate extensions in resource"""
    errors = []
    
    # Collect all extensions
    extensions = collect_extensions(resource)
    
    for extension in extensions:
        url = extension.get('url')
        if not url:
            errors.append("Extension missing required 'url' element")
            continue
        
        try:
            # Load extension definition
            ext_def = load_extension_definition(url)
            
            # Validate extension structure
            ext_errors = validate_extension_structure(extension, ext_def)
            errors.extend(ext_errors)
            
        except Exception as e:
            errors.append(f"Error validating extension {url}: {str(e)}")
    
    return errors

def collect_extensions(resource: dict, path: str = '') -> list:
    """Recursively collect all extensions from resource"""
    extensions = []
    
    if isinstance(resource, dict):
        # Direct extensions
        if 'extension' in resource:
            for ext in resource['extension']:
                extensions.append(ext)
        
        # Primitive extensions (e.g., _birthDate)
        for key, value in resource.items():
            if key.startswith('_') and isinstance(value, dict):
                if 'extension' in value:
                    extensions.extend(value['extension'])
        
        # Recurse into nested objects
        for key, value in resource.items():
            if key not in ['extension'] and not key.startswith('_'):
                if isinstance(value, (dict, list)):
                    nested_extensions = collect_extensions(value, f"{path}.{key}")
                    extensions.extend(nested_extensions)
    
    elif isinstance(resource, list):
        for i, item in enumerate(resource):
            if isinstance(item, dict):
                nested_extensions = collect_extensions(item, f"{path}[{i}]")
                extensions.extend(nested_extensions)
    
    return extensions
```

## Validation Orchestration

### Complete Resource Validation
```python
class FHIRValidator:
    def __init__(self, package_manager):
        self.package_manager = package_manager
        self.structure_loader = StructureDefinitionLoader(package_manager)
        self.terminology_validator = TerminologyValidator(package_manager)
    
    def validate_resource(self, resource: dict, 
                         profile_urls: list = None) -> ValidationResult:
        """Complete FHIR resource validation"""
        all_errors = []
        all_warnings = []
        
        # 1. Structure validation
        structure_result = validate_fhir_structure(resource)
        all_errors.extend(structure_result.errors)
        all_warnings.extend(structure_result.warnings)
        
        # 2. Data type validation
        datatype_errors = self.validate_resource_datatypes(resource)
        all_errors.extend(datatype_errors)
        
        # 3. Profile validation
        if profile_urls:
            for profile_url in profile_urls:
                profile_result = validate_against_profile(
                    resource, profile_url, self.structure_loader
                )
                all_errors.extend(profile_result.errors)
                all_warnings.extend(profile_result.warnings)
        else:
            # Validate against base resource definition
            base_profile_url = f"http://hl7.org/fhir/StructureDefinition/{resource['resourceType']}"
            try:
                profile_result = validate_against_profile(
                    resource, base_profile_url, self.structure_loader
                )
                all_errors.extend(profile_result.errors)
                all_warnings.extend(profile_result.warnings)
            except Exception as e:
                all_warnings.append(f"Could not validate against base profile: {str(e)}")
        
        return ValidationResult(
            valid=(len(all_errors) == 0),
            errors=all_errors,
            warnings=all_warnings
        )
    
    def validate_bundle(self, bundle: dict) -> ValidationResult:
        """Validate FHIR Bundle and all contained resources"""
        all_errors = []
        all_warnings = []
        
        # Validate bundle structure
        bundle_result = self.validate_resource(bundle)
        all_errors.extend(bundle_result.errors)
        all_warnings.extend(bundle_result.warnings)
        
        # Validate each entry
        for i, entry in enumerate(bundle.get('entry', [])):
            if 'resource' in entry:
                resource = entry['resource']
                
                # Extract profile URLs from meta
                profile_urls = resource.get('meta', {}).get('profile', [])
                
                resource_result = self.validate_resource(resource, profile_urls)
                
                # Prefix errors with entry index
                for error in resource_result.errors:
                    all_errors.append(f"Bundle.entry[{i}]: {error}")
                
                for warning in resource_result.warnings:
                    all_warnings.append(f"Bundle.entry[{i}]: {warning}")
        
        return ValidationResult(
            valid=(len(all_errors) == 0),
            errors=all_errors,
            warnings=all_warnings
        )
```

## Performance Optimization

### Validation Caching
```python
from functools import lru_cache
import hashlib

class CachedValidator:
    def __init__(self, base_validator):
        self.base_validator = base_validator
        self.resource_cache = {}
    
    @lru_cache(maxsize=1000)
    def get_structure_definition(self, url: str):
        """Cached StructureDefinition loading"""
        return self.base_validator.structure_loader.load_structure_definition(url)
    
    def validate_resource_cached(self, resource: dict, profile_urls: list = None):
        """Validate with caching for identical resources"""
        # Create hash of resource for caching
        resource_str = json.dumps(resource, sort_keys=True)
        cache_key = hashlib.md5(resource_str.encode()).hexdigest()
        
        if profile_urls:
            cache_key += '_' + '_'.join(sorted(profile_urls))
        
        if cache_key in self.resource_cache:
            return self.resource_cache[cache_key]
        
        result = self.base_validator.validate_resource(resource, profile_urls)
        self.resource_cache[cache_key] = result
        
        return result
```

This reference provides comprehensive patterns for implementing robust FHIR validation in your applications, covering all major aspects from basic structure validation to complex profile and terminology validation.
