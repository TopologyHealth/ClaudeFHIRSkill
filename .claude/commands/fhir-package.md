---
description: Manage FHIR package installation, loading, and dependency resolution
---

You are managing FHIR packages. Follow these steps:

1. **Identify the package operation**:
   - Install a package (from registry or file)
   - List installed packages
   - Load package resources
   - Search for packages
   - Update packages
   - Inspect package contents
2. **Determine package details**:
   - Package ID (e.g., hl7.fhir.r4.core, hl7.fhir.us.core)
   - Version (e.g., 4.0.1, 5.0.1)
   - Source (packages.fhir.org, local file, custom registry)
3. **Check environment**:
   - Identify if using Node.js, Python, or other
   - Check for existing package manager (@fhir/package-loader, fhir-package-loader)
   - Determine cache location (~/.fhir/packages/)
4. **Execute the operation**:
   - For installation: Use appropriate package manager or manual download
   - For listing: Check cache directory or use package manager commands
   - For loading: Provide code to load resources from package
   - For inspection: Read and display package manifest

**Common packages**:
- `hl7.fhir.r4.core@4.0.1` - FHIR R4 core specification
- `hl7.fhir.r5.core@5.0.0` - FHIR R5 core specification
- `hl7.fhir.us.core@5.0.1` - US Core Implementation Guide
- `hl7.fhir.uv.ips@1.1.0` - International Patient Summary
- `hl7.fhir.us.mcode@3.0.0` - Minimal Common Oncology Data Elements

**Package operations**:

**Install**:
```bash
# Node.js
npm install @fhir/package-loader
npx fhir-package-loader install hl7.fhir.r4.core 4.0.1

# Python
pip install fhir-package-loader
fhir-package-loader install hl7.fhir.us.core 5.0.1

# Manual download
curl https://packages.fhir.org/hl7.fhir.r4.core/4.0.1 -o package.tgz
```

**Load in code**:
```typescript
// TypeScript
import { PackageLoader } from '@fhir/package-loader';
const loader = new PackageLoader();
const pkg = await loader.load('hl7.fhir.r4.core', '4.0.1');
```

```python
# Python
from fhir_package_loader import load_package
package = load_package('hl7.fhir.r4.core', '4.0.1')
```

**List installed**:
```bash
ls ~/.fhir/packages/
```

**Package structure**:
- package.json - Manifest with metadata
- package/ - Resource files (StructureDefinition, ValueSet, etc.)
- Contains: profiles, extensions, search parameters, examples

**Provide**:
- Installation commands for user's environment
- Code snippets to load and use package resources
- Guidance on resolving dependencies
- Help finding package versions on packages.fhir.org
