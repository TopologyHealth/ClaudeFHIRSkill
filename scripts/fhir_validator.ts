#!/usr/bin/env node
/**
 * FHIR Resource Validator and Processor
 * Validates FHIR resources against profiles and provides formatting
 */

import { readFileSync, writeFileSync } from 'fs';
import { resolve } from 'path';
import * as yargs from 'yargs';

interface FHIRResource {
  resourceType: string;
  id?: string;
  meta?: {
    profile?: string[];
    versionId?: string;
    lastUpdated?: string;
  };
  [key: string]: any;
}

interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

class FHIRValidator {
  private knownResourceTypes = new Set([
    'Patient', 'Practitioner', 'Organization', 'Location', 'Observation',
    'DiagnosticReport', 'Medication', 'MedicationRequest', 'AllergyIntolerance',
    'Condition', 'Procedure', 'Encounter', 'Appointment', 'Bundle',
    'CapabilityStatement', 'StructureDefinition', 'ValueSet', 'CodeSystem'
  ]);

  validateResource(resource: FHIRResource): ValidationResult {
    const result: ValidationResult = {
      valid: true,
      errors: [],
      warnings: []
    };

    // Basic structure validation
    if (!resource.resourceType) {
      result.errors.push('Missing required field: resourceType');
      result.valid = false;
    } else if (!this.knownResourceTypes.has(resource.resourceType)) {
      result.warnings.push(`Unknown resource type: ${resource.resourceType}`);
    }

    // ID validation
    if (resource.id && !/^[A-Za-z0-9\-\.]{1,64}$/.test(resource.id)) {
      result.errors.push('Invalid ID format - must be 1-64 characters, alphanumeric, hyphens, dots only');
      result.valid = false;
    }

    // Resource-specific validation
    switch (resource.resourceType) {
      case 'Patient':
        this.validatePatient(resource, result);
        break;
      case 'Observation':
        this.validateObservation(resource, result);
        break;
      case 'Bundle':
        this.validateBundle(resource, result);
        break;
    }

    return result;
  }

  private validatePatient(patient: FHIRResource, result: ValidationResult): void {
    // Patient.name validation
    if (patient.name && Array.isArray(patient.name)) {
      patient.name.forEach((name: any, index: number) => {
        if (!name.family && !name.given) {
          result.warnings.push(`Patient.name[${index}]: Should have either family or given name`);
        }
      });
    }

    // Gender validation
    if (patient.gender && !['male', 'female', 'other', 'unknown'].includes(patient.gender)) {
      result.errors.push(`Invalid gender value: ${patient.gender}`);
      result.valid = false;
    }

    // Birth date validation
    if (patient.birthDate && !/^\d{4}-\d{2}-\d{2}$/.test(patient.birthDate)) {
      result.errors.push('Invalid birthDate format - must be YYYY-MM-DD');
      result.valid = false;
    }
  }

  private validateObservation(observation: FHIRResource, result: ValidationResult): void {
    // Status is required
    if (!observation.status) {
      result.errors.push('Observation.status is required');
      result.valid = false;
    } else if (!['registered', 'preliminary', 'final', 'amended', 'corrected', 'cancelled', 'entered-in-error', 'unknown'].includes(observation.status)) {
      result.errors.push(`Invalid status: ${observation.status}`);
      result.valid = false;
    }

    // Code is required
    if (!observation.code) {
      result.errors.push('Observation.code is required');
      result.valid = false;
    }

    // Subject reference validation
    if (!observation.subject) {
      result.errors.push('Observation.subject is required');
      result.valid = false;
    } else if (observation.subject.reference && !observation.subject.reference.includes('/')) {
      result.warnings.push('Subject reference should include resource type (e.g., Patient/123)');
    }
  }

  private validateBundle(bundle: FHIRResource, result: ValidationResult): void {
    // Type is required
    if (!bundle.type) {
      result.errors.push('Bundle.type is required');
      result.valid = false;
    }

    // Entry validation
    if (bundle.entry && Array.isArray(bundle.entry)) {
      bundle.entry.forEach((entry: any, index: number) => {
        if (entry.resource) {
          const entryValidation = this.validateResource(entry.resource);
          if (!entryValidation.valid) {
            result.errors.push(`Bundle.entry[${index}]: ${entryValidation.errors.join(', ')}`);
            result.valid = false;
          }
        }
      });
    }
  }

  formatResource(resource: FHIRResource, options: { indent?: number } = {}): string {
    const indent = options.indent || 2;
    
    // Ensure proper ordering of common FHIR fields
    const ordered: any = {};
    
    // Standard order for FHIR resources
    const fieldOrder = ['resourceType', 'id', 'meta', 'identifier', 'active', 'name', 'status', 'code', 'subject', 'entry'];
    
    fieldOrder.forEach(field => {
      if (resource[field] !== undefined) {
        ordered[field] = resource[field];
      }
    });
    
    // Add remaining fields
    Object.keys(resource).forEach(key => {
      if (!fieldOrder.includes(key)) {
        ordered[key] = resource[key];
      }
    });
    
    return JSON.stringify(ordered, null, indent);
  }

  generateExample(resourceType: string): FHIRResource | null {
    const examples: Record<string, FHIRResource> = {
      Patient: {
        resourceType: 'Patient',
        id: 'example',
        active: true,
        name: [{
          family: 'Doe',
          given: ['John']
        }],
        gender: 'male',
        birthDate: '1990-01-01'
      },
      Observation: {
        resourceType: 'Observation',
        id: 'example',
        status: 'final',
        code: {
          coding: [{
            system: 'http://loinc.org',
            code: '55284-4',
            display: 'Blood pressure systolic & diastolic'
          }]
        },
        subject: {
          reference: 'Patient/example'
        },
        valueQuantity: {
          value: 120,
          unit: 'mmHg',
          system: 'http://unitsofmeasure.org',
          code: 'mm[Hg]'
        }
      },
      Bundle: {
        resourceType: 'Bundle',
        id: 'example',
        type: 'collection',
        entry: [{
          resource: {
            resourceType: 'Patient',
            id: 'patient1',
            active: true,
            name: [{
              family: 'Example',
              given: ['Patient']
            }]
          }
        }]
      }
    };

    return examples[resourceType] || null;
  }
}

// CLI Interface
async function main() {
  const argv = yargs
    .command('validate <file>', 'Validate a FHIR resource file', (yargs) => {
      yargs.positional('file', {
        describe: 'Path to FHIR resource JSON file',
        type: 'string'
      });
    })
    .command('format <file>', 'Format a FHIR resource file', (yargs) => {
      yargs
        .positional('file', {
          describe: 'Path to FHIR resource JSON file',
          type: 'string'
        })
        .option('output', {
          alias: 'o',
          describe: 'Output file path',
          type: 'string'
        })
        .option('indent', {
          alias: 'i',
          describe: 'Indentation spaces',
          type: 'number',
          default: 2
        });
    })
    .command('example <resourceType>', 'Generate example FHIR resource', (yargs) => {
      yargs.positional('resourceType', {
        describe: 'FHIR resource type',
        type: 'string'
      });
    })
    .demandCommand()
    .help()
    .argv;

  const validator = new FHIRValidator();

  try {
    if (argv._[0] === 'validate') {
      const filePath = resolve(argv.file as string);
      const content = readFileSync(filePath, 'utf8');
      const resource: FHIRResource = JSON.parse(content);
      
      const result = validator.validateResource(resource);
      
      console.log(`\nValidating ${resource.resourceType}/${resource.id || 'unknown'}:`);
      
      if (result.valid) {
        console.log('✅ Valid FHIR resource');
      } else {
        console.log('❌ Invalid FHIR resource');
        result.errors.forEach(error => console.log(`  Error: ${error}`));
      }
      
      if (result.warnings.length > 0) {
        console.log('\nWarnings:');
        result.warnings.forEach(warning => console.log(`  Warning: ${warning}`));
      }
      
      process.exit(result.valid ? 0 : 1);
    }
    
    else if (argv._[0] === 'format') {
      const filePath = resolve(argv.file as string);
      const content = readFileSync(filePath, 'utf8');
      const resource: FHIRResource = JSON.parse(content);
      
      const formatted = validator.formatResource(resource, { indent: argv.indent as number });
      
      if (argv.output) {
        writeFileSync(resolve(argv.output as string), formatted);
        console.log(`Formatted resource written to ${argv.output}`);
      } else {
        console.log(formatted);
      }
    }
    
    else if (argv._[0] === 'example') {
      const resourceType = argv.resourceType as string;
      const example = validator.generateExample(resourceType);
      
      if (example) {
        const formatted = validator.formatResource(example);
        console.log(formatted);
      } else {
        console.log(`No example available for resource type: ${resourceType}`);
        process.exit(1);
      }
    }
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

export { FHIRValidator };
