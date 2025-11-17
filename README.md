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
