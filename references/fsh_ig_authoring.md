# FHIR Shorthand (FSH) & IG Authoring Reference

Comprehensive reference for authoring FHIR Implementation Guides using FSH (FHIR Shorthand), SUSHI, and GoFSH.

## Toolchain Overview

| Tool | Purpose | Install |
|------|---------|---------|
| **SUSHI** | FSH compiler → FHIR JSON | `npm install -g fsh-sushi` |
| **GoFSH** | FHIR JSON → FSH converter | `npm install -g gofsh` |
| **IG Publisher** | Produces the IG website from SUSHI output | Downloaded via `_updatePublisher.sh` |

Prerequisites: Node.js LTS. Verify with `node --version` and `npm --version`.

---

## SUSHI CLI

```bash
# Initialize a new IG project scaffold
sushi init

# Build FSH → FHIR JSON (run from project root)
sushi build

# Build with options
sushi build . --snapshot           # Include full StructureDefinition snapshot
sushi build . --log-level debug    # Verbose output
sushi build . --out ./output       # Custom output directory
sushi build . --preprocessed       # Debug: dump resolved aliases/rulesets

# Other commands
sushi --version
sushi help
sushi help build
sushi update-dependencies          # Bump deps to latest
```

Output lands in `fsh-generated/resources/` as `{ResourceType}-{id}.json` files. **Warning: SUSHI deletes and regenerates this folder on every run.**

---

## GoFSH CLI

Convert existing FHIR JSON conformance artifacts to FSH.

```bash
# Basic conversion (input dir contains JSON resources)
gofsh ./path/to/fhir-resources

# With dependencies beyond R4
gofsh ./definitions -d hl7.fhir.us.core@3.1.0 -d hl7.fhir.uv.ips@1.0.0

# Load existing aliases file to reuse
gofsh ./definitions --alias-file ./aliases.fsh

# Validate round-trip (GoFSH → SUSHI compare)
gofsh ./definitions --fshing-trip

# Output styles
gofsh ./definitions --style file-per-definition   # default: one file per definition
gofsh ./definitions --style group-by-fsh-type     # grouped by FSH entity type
gofsh ./definitions --style group-by-profile      # profile + related items together
gofsh ./definitions --style single-file           # everything in one file

# Indented rule output (cleaner for complex profiles)
gofsh ./definitions --indent

# Control InstanceOf derivation from meta.profile
gofsh ./definitions --meta-profile only-one   # default
gofsh ./definitions --meta-profile first
gofsh ./definitions --meta-profile none
```

GoFSH outputs an `input/fsh/` directory, `index.txt`, and a starter `sushi-config.yaml`.

---

## Project Structure

### Minimal FSH-only project
```
my-project/
├── sushi-config.yaml
└── input/
    └── fsh/
        ├── profiles.fsh
        ├── extensions.fsh
        ├── valuesets.fsh
        └── instances.fsh
```

### Full IG Publisher-compatible project
```
my-project/
├── sushi-config.yaml
├── ig.ini                          # Required for IG Publisher
├── package-list.json               # IG version history
├── _genonce.sh / _genonce.bat      # Run IG Publisher
├── _updatePublisher.sh / .bat      # Download latest IG Publisher
├── .gitignore
├── input/
│   ├── fsh/                        # All .fsh source files
│   │   ├── profiles.fsh
│   │   ├── extensions.fsh
│   │   ├── valuesets.fsh
│   │   ├── codesystems.fsh
│   │   ├── instances.fsh
│   │   └── aliases.fsh             # Centralize alias definitions
│   ├── pagecontent/                # Narrative markdown/XML pages
│   │   ├── index.md                # Home page
│   │   ├── 1_background.md         # Numbered = TOC order
│   │   ├── {resource-id}-intro.md  # Injected before artifact def
│   │   └── {resource-id}-notes.md  # Injected after artifact def
│   ├── images/                     # Images, PDFs, spreadsheets
│   │   └── diagram.png
│   ├── includes/
│   │   └── menu.xml                # Custom navigation menu
│   └── ignoreWarnings.txt          # Suppress IG Publisher QA warnings
├── sushi-ignoreErrors.txt          # Suppress SUSHI errors
├── sushi-ignoreWarnings.txt        # Suppress SUSHI warnings
└── fsh-generated/                  # SUSHI output (do not edit manually)
    └── resources/
        ├── StructureDefinition-my-profile.json
        ├── ValueSet-my-valueset.json
        └── ImplementationGuide-my.ig.json
```

---

## sushi-config.yaml Reference

```yaml
# --- Required fields ---
id: hl7.fhir.us.example          # Package identifier
canonical: http://hl7.org/fhir/us/example  # Base canonical URL
name: ExampleIG                  # No spaces
status: draft                    # draft | active | retired | unknown
version: 0.1.0
fhirVersion: 4.0.1               # 4.0.1 | 5.0.0 | etc.

# --- Strongly recommended ---
title: "Example Implementation Guide"
description: "An example IG for demonstration purposes."
copyrightYear: 2024+
releaseLabel: ci-build            # ci-build | STU1 | Normative 1 | etc.
license: CC0-1.0                  # SPDX identifier

# --- Publisher / Contact ---
publisher:
  name: HL7 International
  url: http://hl7.org
  email: fhir@lists.hl7.org

contact:
  - name: Jane Smith
    telecom:
      - system: email
        value: jane@example.org

# --- Jurisdiction ---
jurisdiction: urn:iso:std:iso:3166#US "United States"

# --- Dependencies ---
dependencies:
  hl7.fhir.us.core: 6.1.0
  hl7.terminology.r4: 5.5.0
  # Special versions:
  # dev      → local FHIR cache
  # current  → latest CI build
  # current$branch → specific branch CI build

  # Advanced with id alias for FSH use:
  hl7.fhir.us.core:
    id: uscore
    uri: http://hl7.org/fhir/us/core/ImplementationGuide/hl7.fhir.us.core
    version: 6.1.0

# --- Global profiles (applied to all resources of type) ---
global:
  Patient: http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient

# --- Navigation menu ---
menu:
  Home: index.html
  Background: background.html
  Artifacts:
    Profiles: artifacts.html#structures-resource-profiles
    Extensions: artifacts.html#structures-extension-definitions
    Value Sets: artifacts.html#terminology-value-sets
  Downloads: downloads.html

# --- Pages ---
pages:
  index.md:
    title: Home
  background.md:
    title: Background
  downloads.md:
    title: Downloads and Links

# --- IG Publisher parameters ---
parameters:
  show-inherited-invariants: false
  excludettl: true
  validation: [allow-any-extensions, no-broken-links]

# --- Resource overrides ---
resources:
  Patient/example-patient:
    name: Example Patient
    description: "An example patient resource"
    exampleBoolean: true        # R4
    # isExample: true           # R5
  StructureDefinition/omit-this: omit   # Exclude from IG

# --- Groups (organize artifacts) ---
groups:
  PatientGroup:
    name: Patient Profiles
    description: Profiles related to the Patient resource
    resources:
      - StructureDefinition/my-patient-profile

# --- Instance generation options ---
instanceOptions:
  setMetaProfile: always        # always | never | inline-only | standalone-only
  setId: always                 # always | standalone-only
  manualSliceOrdering: false

# --- FSH Only mode (no IG processing) ---
# FSHOnly: true
```

---

## FSH Language Reference

### Aliases

Declare at top of any `.fsh` file. By convention, prefix with `$`.

```
Alias: $LNC = http://loinc.org
Alias: $SCT = http://snomed.info/sct
Alias: $UCUM = http://unitsofmeasure.org
Alias: $V2 = http://terminology.hl7.org/CodeSystem/v2-0203
Alias: $USCoreRace = http://hl7.org/fhir/us/core/StructureDefinition/us-core-race
```

### Comments

```
// Single-line comment

/* Multi-line
   block comment */
```

### Triple-Quoted Strings

For multi-line descriptions/purposes:
```
* ^purpose = """
    * Intended for workflows where:
      * this happens; or
      * that happens
  """
```

---

## Entity Types

### Profile

```
Profile: MyPatientProfile
Parent: Patient                          // or URL or alias
Id: my-patient-profile
Title: "My Patient Profile"
Description: "A constrained Patient for our IG"
* identifier 1..* MS
* name 1..* MS
* birthDate MS
* gender 1..1 MS
* gender from http://hl7.org/fhir/ValueSet/administrative-gender (required)
```

### Extension

**Simple (value-bearing):**
```
Extension: PatientReligion
Id: patient-religion
Title: "Patient Religion"
Description: "The religious affiliation of the patient"
Context: Patient
* value[x] only CodeableConcept
* value[x] from ReligionValueSet (extensible)
```

**Complex (sub-extensions):**
```
Extension: USCoreEthnicityExtension
Id: us-core-ethnicity
Title: "US Core Ethnicity Extension"
Context: Patient, RelatedPerson, Practitioner, Person
* extension contains
    ombCategory 0..1 MS and
    detailed 0..* and
    text 1..1 MS
* extension[ombCategory].value[x] only Coding
* extension[ombCategory].value[x] from OmbEthnicityCategories (required)
* extension[ombCategory] ^short = "Hispanic or Latino|Not Hispanic or Latino"
* extension[detailed].value[x] only Coding
* extension[detailed].value[x] from DetailedEthnicity (extensible)
* extension[text].value[x] only string
* extension[text] ^short = "Ethnicity Text"
```

**Context syntax:**
```
Context: Patient                                    // simple element
Context: Patient.contact.telecom                    // nested element
Context: "Patient.contact where use = 'home'"       // FHIRPath
Context: Patient, RelatedPerson, Practitioner       // multiple
```

### Instance

```
Instance: JaneDoe
InstanceOf: MyPatientProfile
Title: "Jane Doe"
Description: "Example patient Jane Doe"
Usage: #example
* identifier[0].system = "http://hospital.example.org/mrns"
* identifier[0].value = "12345"
* name[0].family = "Doe"
* name[0].given[0] = "Jane"
* birthDate = 1970-01-01
* gender = #female
* extension[patient-religion].valueCodeableConcept = $SCT#160538000 "Christian"
```

Usage codes: `#example` (default), `#definition` (appears on own IG page), `#inline` (contained only).

### ValueSet

```
ValueSet: MyConditionStatusVS
Id: my-condition-status
Title: "My Condition Status Value Set"
Description: "Status codes for conditions in our IG"
* include codes from system $SCT where concept is-a #404684003   // Clinical finding
* include $V3#active "Active"
* include $V3#inactive "Inactive"
* exclude $SCT#74964007 "Other"
```

### CodeSystem

```
CodeSystem: MyCustomCodes
Id: my-custom-codes
Title: "My Custom Code System"
Description: "Codes defined for this IG"
* #pending "Pending" "Awaiting review"
* #approved "Approved" "Formally approved"
* #rejected "Rejected" "Not approved"
```

Hierarchical codes:
```
CodeSystem: AnatomyCS
* #body "Body" "The body"
  * #head "Head" "The head"
    * #eye "Eye" "The eye"
  * #arm "Arm" "The arm"
```

### Invariant

```
Invariant: my-inv-1
Description: "If category is 'vital-signs', value must be present"
Severity: #error
Expression: "category.coding.code = 'vital-signs' implies value.exists()"
```

Reference in a Profile:
```
* obeys my-inv-1
```

### Mapping

```
Mapping: MyPatientToV2
Source: MyPatientProfile
Target: "http://hl7.org/v2"
Id: my-patient-v2-map
Title: "Patient to HL7 v2 Mapping"
* -> "PID"
* name -> "PID-5 (family), PID-9 (given)"
* birthDate -> "PID-7"
* gender -> "PID-8"
```

### Logical Model

```
Logical: ClinicalAssessment
Id: clinical-assessment
Title: "Clinical Assessment"
Description: "Logical model for a clinical assessment document"
* assessmentDate 1..1 dateTime "Date of assessment" "When performed"
* assessor 1..* Reference(Practitioner) "Assessor" "Who performed"
* findings 0..* BackboneElement "Findings" "Clinical findings"
  * code 1..1 CodeableConcept "Finding code" "What was found"
  * value[x] 0..1 string or Quantity "Finding value" "Result"
```

### RuleSet (Reusable Rules)

**Simple RuleSet:**
```
RuleSet: PublicationMetadata
* ^status = #active
* ^experimental = false
* ^publisher = "My Organization"
* ^date = "2024-01-01"

// Usage:
Profile: MyProfile
Parent: Observation
* insert PublicationMetadata
```

**Parameterized RuleSet:**
```
RuleSet: SetContext(contextPath)
* ^context[+].type = #element
* ^context[=].expression = "{contextPath}"

// Usage:
Extension: MyExtension
* insert SetContext(Patient)
* insert SetContext(Practitioner)
```

---

## Rules Reference

### Cardinality
```
* element 0..1        // Optional, at most one
* element 1..*        // At least one, unbounded
* element 1..1        // Exactly one
* element 0..*        // Optional, unbounded (default)
```

### Flags
```
* element MS          // Must Support
* element SU          // Summary (include in _summary)
* element ?!          // Is Modifier
* element N           // Normative
* element TU          // Trial Use
* element D           // Draft
// Combine:
* element 1..* MS SU
```

### Type Constraint
```
* value[x] only Quantity
* value[x] only Quantity or CodeableConcept
* performer only Reference(Practitioner or Organization)
```

### Binding
```
* code from http://hl7.org/fhir/ValueSet/observation-codes (required)
* status from ObservationStatusVS (extensible)
* category from $ObsCat (preferred)
* method from MethodVS (example)
```

### Assignment (Fixed / Default Values)
```
// Code
* status = #final

// Coding with system
* code = $LNC#29463-7 "Body weight"

// Coding with alias
* code = $SCT#27113001 "Body weight"

// Quantity
* valueQuantity = 70 'kg' "kg"

// Boolean, String, Integer, Decimal
* active = true
* name = "Default Name"
* multipleBirthInteger = 2
* score = 9.5

// Reference to profile type
* subject only Reference(MyPatientProfile)

// Canonical
* instantiatesCanonical = Canonical(MyPlanDefinition)
```

### Slicing (Contains)
```
// Slice a repeating element
* category contains
    VSCat 1..1 MS

// Set discriminator via caret
* category ^slicing.discriminator[0].type = #pattern
* category ^slicing.discriminator[0].path = "$this"
* category ^slicing.rules = #open

// Constrain the slice
* category[VSCat].coding 1..* MS
* category[VSCat].coding.system 1..1 MS
* category[VSCat].coding.system = "http://terminology.hl7.org/CodeSystem/observation-category"
* category[VSCat].coding.code 1..1 MS
* category[VSCat].coding.code = #vital-signs
```

### Extension Slicing (Profile adding extensions)
```
// Add a standalone extension to a profile
* extension contains
    $USCoreRace named race 0..1 MS and
    $USCoreEthnicity named ethnicity 0..1 MS

* extension[race] ^short = "US Core Race Extension"
```

### Caret Rules (Metadata / ElementDefinition properties)
```
// StructureDefinition metadata
* ^url = "http://example.org/StructureDefinition/my-profile"
* ^version = "1.0.0"
* ^experimental = false
* ^purpose = "Defines constraints for our use case"

// ElementDefinition properties
* code ^binding.description = "Codes for conditions"
* name ^example[0].label = "Example name"
* name ^example[0].valueHumanName.family = "Smith"

// Self element (the root)
* . ^short = "Profile root short description"
* . ^comment = "Extended comment on the profile root"
```

### ValueSet Include/Exclude Rules
```
// Include entire code system
* include codes from system http://loinc.org

// Include specific concepts
* $SCT#73211009 "Diabetes mellitus"
* $SCT#44054006 "Diabetes mellitus type 2"

// Include by filter
* include codes from system $SCT where concept is-a #73211009

// Include another ValueSet
* include codes from valueset http://hl7.org/fhir/ValueSet/condition-code

// Exclude
* exclude codes from system http://loinc.org where STATUS = DEPRECATED
```

---

## Path Grammar

| Pattern | Example | Meaning |
|---------|---------|---------|
| Simple element | `status` | Direct child element |
| Nested | `name.family` | Nested element |
| Choice type | `valueQuantity` | `value[x]` as Quantity |
| Array index | `name[0]` | First item (zero-based) |
| Soft index (increment) | `name[+]` | Next slot |
| Soft index (same) | `name[=]` | Same slot as previous |
| Slice | `component[respirationScore]` | Named slice |
| Slice + index | `component[respirationScore][1]` | Second item in slice |
| Extension | `extension[race]` | Extension slice by name |
| Extension by URL | `extension[http://hl7.org/fhir/us/core/StructureDefinition/us-core-race]` | By full URL |
| Reference target | `performer[Practitioner]` | Specific Reference type |
| Caret (metadata) | `^experimental` | StructureDefinition property |
| Element metadata | `status ^short` | ElementDefinition property |

---

## Code / Coding / Quantity Syntax

```
// Simple code (no system)
#active
#"code with spaces"

// Coding: system#code "display"
http://loinc.org#29463-7 "Body Weight"
$LNC#29463-7 "Body Weight"

// Coding with version
http://loinc.org|2.73#29463-7

// Quantity (UCUM)
70.5 'kg' "kg"
98.6 '[degF]' "F"

// Quantity (non-UCUM system)
155 http://unitsofmeasure.org#C48531 "Pound"
```

---

## Complete Worked Example

```
// aliases.fsh
Alias: $LNC = http://loinc.org
Alias: $SCT = http://snomed.info/sct
Alias: $UCUM = http://unitsofmeasure.org

// profiles.fsh
Profile: VitalSignsObservation
Parent: http://hl7.org/fhir/StructureDefinition/vitalsigns
Id: vital-signs-observation
Title: "Vital Signs Observation"
Description: "Constrained vital signs profile for our IG"
* insert PublicationMetadata
* status MS
* category MS
* code MS
* subject 1..1 MS
* subject only Reference(MyPatientProfile)
* effective[x] 1..1 MS
* effective[x] only dateTime or Period
* value[x] MS
* value[x] only Quantity
* valueQuantity.value 1..1 MS
* valueQuantity.unit 1..1 MS
* valueQuantity.system 1..1 MS
* valueQuantity.system = $UCUM
* valueQuantity.code 1..1 MS

// rulesets.fsh
RuleSet: PublicationMetadata
* ^status = #active
* ^experimental = false
* ^publisher = "My Organization"

// invariants.fsh
Invariant: vs-quantity-present
Description: "Value quantity must have value and unit when present"
Severity: #error
Expression: "valueQuantity.exists() implies (valueQuantity.value.exists() and valueQuantity.unit.exists())"

// instances.fsh
Instance: BloodPressureExample
InstanceOf: VitalSignsObservation
Title: "Blood Pressure Example"
Usage: #example
* status = #final
* category[VSCat].coding.system = "http://terminology.hl7.org/CodeSystem/observation-category"
* category[VSCat].coding.code = #vital-signs
* code = $LNC#85354-9 "Blood pressure systolic and diastolic"
* subject = Reference(JaneDoe)
* effectiveDateTime = "2024-01-15T10:30:00Z"
* component[+].code = $LNC#8480-6 "Systolic blood pressure"
* component[=].valueQuantity = 120 'mm[Hg]' "mmHg"
* component[+].code = $LNC#8462-4 "Diastolic blood pressure"
* component[=].valueQuantity = 80 'mm[Hg]' "mmHg"
```

---

## Common IG Authoring Workflows

### Start a new IG from scratch
```bash
mkdir my-ig && cd my-ig
sushi init                   # Interactive scaffold generator
# Edit sushi-config.yaml
# Write .fsh files in input/fsh/
sushi build                  # Compile FSH → JSON
./_genonce.sh                # Run IG Publisher (first run downloads it)
```

### Migrate existing FHIR JSON to FSH
```bash
# Point GoFSH at existing JSON conformance artifacts
gofsh ./existing-ig/resources \
  -d hl7.fhir.us.core@6.1.0 \
  --style group-by-profile \
  --indent \
  --fshing-trip              # Validate round-trip accuracy

# Review output in ./fsh-output/input/fsh/
# Then move to your project's input/fsh/
```

### Debug a failing build
```bash
sushi build --log-level debug
sushi build --preprocessed   # See resolved aliases/rulesets in _preprocessed/
```

### Update IG Publisher
```bash
./_updatePublisher.sh        # Downloads latest jar
```

---

## Best Practices

### File Organization
- `aliases.fsh` — All `Alias:` declarations (one place to update URLs)
- `profiles.fsh` — Profile definitions
- `extensions.fsh` — Extension definitions
- `valuesets.fsh` — ValueSet and CodeSystem definitions
- `instances.fsh` — Example instances (Usage: #example)
- `rulesets.fsh` — Shared RuleSets
- `invariants.fsh` — Invariant definitions

### Naming Conventions
- **Item names** (Profile, Extension, etc.): `PascalCase` (e.g., `MyPatientProfile`)
- **Item IDs**: `kebab-case`, max 64 chars (e.g., `my-patient-profile`)
- **Slice names**: `lowerCamelCase` (e.g., `respirationScore`)
- **Aliases**: Prefix with `$` (e.g., `$LNC`, `$SCT`)
- **RuleSets**: `PascalCase`, descriptive (e.g., `PublicationMetadata`)

### Slicing Order
Always define slices (Contains rule) **before** constraining individual slices:
```
// 1. First: declare the slices
* component contains
    systolic 1..1 MS and
    diastolic 1..1 MS

// 2. Then: constrain each slice
* component[systolic].code = $LNC#8480-6
* component[diastolic].code = $LNC#8462-4
```

### Extension Order
Always declare extension slices before constraining sub-elements:
```
// 1. Declare
* extension contains
    ombCategory 0..1 MS and
    text 1..1 MS

// 2. Constrain
* extension[ombCategory].value[x] only Coding
* extension[text].value[x] only string
```

### Must Support Strategy
Flag elements as MS based on your IG's definition. Be explicit:
```
* identifier 1..* MS
* identifier.system 1..1 MS
* identifier.value 1..1 MS
```

### Canonical URLs
Keep consistent with your `canonical` in sushi-config.yaml. SUSHI automatically generates canonical URLs using `{canonical}/StructureDefinition/{id}`.

### Dependencies
Pin exact versions for reproducible builds. Use `current` only for development against unreleased IGs.

---

## Key FSH Spec Links

- Full Spec: https://build.fhir.org/ig/HL7/fhir-shorthand/
- Language Reference: https://build.fhir.org/ig/HL7/fhir-shorthand/reference.html
- SUSHI Docs: https://fshschool.org/docs/sushi/
- GoFSH Docs: https://fshschool.org/docs/gofsh/
- FSH School (tutorials): https://fshschool.org/
