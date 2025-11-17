# FHIR Software Development Skill

A comprehensive Claude Code skill for building FHIR (Fast Healthcare Interoperability Resources) software systems with expert guidance on implementation, validation, and healthcare data exchange.

## Overview

This skill provides specialized assistance for FHIR development across multiple versions (R4, R4B, R5) and programming languages. It includes expert knowledge of:

- FHIR resource modeling and validation
- Implementation Guide (IG) development
- FHIR server and client implementation
- SMART on FHIR integration
- Terminology services and validation
- Healthcare API development

## When to Use This Skill

Invoke this skill when working on:

- **FHIR API Development**: Building REST APIs that comply with FHIR specifications
- **Healthcare Applications**: Apps that need to process or exchange FHIR resources
- **FHIR Servers/Clients**: Implementing FHIR-compliant servers or client applications
- **Data Validation**: Validating resources against FHIR profiles and Implementation Guides
- **SMART on FHIR Apps**: Healthcare applications using SMART launch workflows
- **Terminology Integration**: Working with ValueSets, CodeSystems, and terminology services
- **Profile Development**: Creating custom FHIR profiles and Implementation Guides

## Features

### Core Capabilities

- **Package Management**: Guidance on using FHIR package loaders and managing local package caches
- **Resource Modeling**: Best practices for modeling FHIR resources in TypeScript, Python, and other languages
- **Server Implementation**: Patterns for FastAPI, Express, and other frameworks
- **Search Implementation**: FHIR search parameter processing and query parsing
- **Validation**: Profile validation, terminology validation, and constraint checking
- **SMART on FHIR**: OAuth 2.0 workflows and app launch sequences
- **Testing**: Unit testing patterns and integration testing for FHIR APIs

### Language Support

- **TypeScript/Node.js**: Express, FHIR TypeScript types, package loaders
- **Python**: FastAPI, Pydantic, fhir.resources library
- Support for other languages with FHIR libraries

### FHIR Versions

- FHIR R4 (4.0.1)
- FHIR R4B
- FHIR R5
- Implementation Guide compatibility

## Installation

Add this skill to your Claude Code environment by placing the `SKILL.md` file in your project's `.claude/skills/` directory or your global skills directory.

## Slash Commands

This skill includes convenient slash commands for common FHIR development tasks:

### `/fhir-validate`

Validate a FHIR resource file against a profile or the base FHIR specification.

**Usage:**

```
/fhir-validate patient.json
```

Checks for:

- Valid resourceType and structure
- Required fields presence
- Data type correctness (dates, codes, references)
- Cardinality constraints
- Terminology bindings (if profile specified)
- Extension validity

### `/fhir-create-resource`

Generate a FHIR resource template with proper structure and example data.

**Usage:**

```
/fhir-create-resource Patient
/fhir-create-resource Observation with US Core profile
/fhir-create-resource Medication in TypeScript
```

Supports:

- All FHIR resource types
- Multiple output formats (JSON, TypeScript, Python)
- Profile-specific templates (US Core, etc.)
- Code generation with validation

### `/fhir-search`

Help construct FHIR search queries with proper parameters and syntax.

**Usage:**

```
/fhir-search find patients by name and birthdate
/fhir-search observations with _include
/fhir-search medications as curl command
```

Provides:

- Properly formatted search URLs
- Correct parameter syntax (string, token, date, reference)
- Query modifiers (\_include, \_revinclude, \_sort, \_count)
- Code snippets for various languages

### `/fhir-package`

Manage FHIR package installation, loading, and dependency resolution.

**Usage:**

```
/fhir-package install hl7.fhir.us.core
/fhir-package list installed
/fhir-package load hl7.fhir.r4.core in Python
```

Handles:

- Package installation from registry
- Cache management
- Loading packages in code
- Inspecting package contents

### `/fhir-test`

Generate comprehensive test cases for FHIR resources and APIs.

**Usage:**

```
/fhir-test create unit tests for Patient validation
/fhir-test API tests for /Patient endpoint
/fhir-test generate test fixtures
```

Generates:

- Unit tests for resource validation
- Integration tests for API endpoints
- CRUD operation tests
- Search functionality tests
- Profile conformance tests
- Test fixtures with realistic data

## Usage Examples

### Example 1: Building a FHIR Server Endpoint

```
I need to create a FHIR Patient endpoint in Python using FastAPI
```

The skill will provide guidance on:
- Setting up FastAPI with fhir.resources
- Implementing CRUD operations
- Validation patterns
- Error handling with OperationOutcome

### Example 2: Validating Against a Profile

```
How do I validate a Patient resource against the US Core Patient profile?
```

Or use the slash command:

```
/fhir-validate patient.json against US Core
```

The skill will guide you through:
- Loading the US Core package
- Setting up profile validation
- Checking must-support elements
- Terminology binding validation

### Example 3: SMART on FHIR Integration

```
I need to implement SMART on FHIR authorization for my app
```

The skill provides:
- OAuth 2.0 configuration
- Authorization code flow implementation
- Token exchange patterns
- Scope management

## Key Patterns Covered

- **Package/Specification Management**: Local caching, package resolution, document indexing
- **Resource Modeling**: Type-safe models with validation
- **Search Implementation**: Parameter parsing, query building, _include/_revinclude
- **Batch/Transaction Processing**: Bundle handling with proper transaction semantics
- **Error Handling**: Proper OperationOutcome generation
- **Testing**: Unit and integration testing patterns

## Resources Referenced

- [FHIR Specification](https://hl7.org/fhir/)
- [Implementation Guide Registry](https://fhir.org/guides/registry/)
- FHIR Package Registry
- US Core Implementation Guide
- SMART on FHIR Specification

## Contributing

Contributions to improve this skill are welcome! Please ensure any additions:
- Follow FHIR specification guidelines
- Include working code examples
- Cover common use cases
- Support multiple programming languages where applicable

## License

This skill is provided as-is for use with Claude Code.

## Support

For issues or questions about using this skill with Claude Code, please refer to the [Claude Code documentation](https://code.claude.com/docs/).

For FHIR specification questions, consult the [official FHIR documentation](https://hl7.org/fhir/) or the [FHIR community chat](https://chat.fhir.org/).
