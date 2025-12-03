# SMART on FHIR Implementation Reference

This document provides comprehensive guidance for implementing SMART on FHIR applications and authorization flows.

## SMART App Launch Framework

### Authorization Code Flow

#### 1. Discovery
The SMART app discovers the authorization and token endpoints from the FHIR server's well-known configuration.

```javascript
// Discover SMART configuration
async function discoverSmartConfig(fhirBaseUrl) {
  const configUrl = `${fhirBaseUrl}/.well-known/smart_configuration`;
  
  try {
    const response = await fetch(configUrl);
    const config = await response.json();
    
    return {
      authorizationEndpoint: config.authorization_endpoint,
      tokenEndpoint: config.token_endpoint,
      capabilities: config.capabilities || [],
      scopesSupported: config.scopes_supported || [],
      responseTypesSupported: config.response_types_supported || []
    };
  } catch (error) {
    // Fallback to CapabilityStatement discovery
    return await discoverFromCapabilityStatement(fhirBaseUrl);
  }
}

async function discoverFromCapabilityStatement(fhirBaseUrl) {
  const capabilityUrl = `${fhirBaseUrl}/metadata`;
  const response = await fetch(capabilityUrl);
  const capability = await response.json();
  
  const smartExtension = capability.rest?.[0]?.security?.extension?.find(
    ext => ext.url === 'http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris'
  );
  
  if (smartExtension) {
    const authExt = smartExtension.extension.find(e => e.url === 'authorize');
    const tokenExt = smartExtension.extension.find(e => e.url === 'token');
    
    return {
      authorizationEndpoint: authExt?.valueUri,
      tokenEndpoint: tokenExt?.valueUri,
      capabilities: [],
      scopesSupported: [],
      responseTypesSupported: ['code']
    };
  }
  
  throw new Error('SMART configuration not found');
}
```

#### 2. Authorization Request
```javascript
function buildAuthorizationUrl(smartConfig, appConfig) {
  const authUrl = new URL(smartConfig.authorizationEndpoint);
  const state = generateSecureRandom(32);
  const codeVerifier = generateCodeVerifier();
  const codeChallenge = generateCodeChallenge(codeVerifier);
  
  // Store for later use
  sessionStorage.setItem('smart_state', state);
  sessionStorage.setItem('code_verifier', codeVerifier);
  
  authUrl.searchParams.set('response_type', 'code');
  authUrl.searchParams.set('client_id', appConfig.clientId);
  authUrl.searchParams.set('redirect_uri', appConfig.redirectUri);
  authUrl.searchParams.set('launch', appConfig.launchToken); // For EHR launch
  authUrl.searchParams.set('scope', appConfig.scopes.join(' '));
  authUrl.searchParams.set('state', state);
  authUrl.searchParams.set('aud', appConfig.fhirBaseUrl);
  
  // PKCE parameters
  authUrl.searchParams.set('code_challenge', codeChallenge);
  authUrl.searchParams.set('code_challenge_method', 'S256');
  
  return authUrl.toString();
}

function generateCodeVerifier() {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return base64urlEncode(array);
}

function generateCodeChallenge(verifier) {
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);
  return crypto.subtle.digest('SHA-256', data).then(hash => base64urlEncode(new Uint8Array(hash)));
}
```

#### 3. Token Exchange
```javascript
async function exchangeCodeForToken(authCode, smartConfig, appConfig) {
  const codeVerifier = sessionStorage.getItem('code_verifier');
  
  const tokenRequest = {
    grant_type: 'authorization_code',
    client_id: appConfig.clientId,
    code: authCode,
    redirect_uri: appConfig.redirectUri,
    code_verifier: codeVerifier
  };
  
  const response = await fetch(smartConfig.tokenEndpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Accept': 'application/json'
    },
    body: new URLSearchParams(tokenRequest)
  });
  
  if (!response.ok) {
    throw new Error(`Token exchange failed: ${response.statusText}`);
  }
  
  const tokenResponse = await response.json();
  
  return {
    accessToken: tokenResponse.access_token,
    tokenType: tokenResponse.token_type || 'Bearer',
    expiresIn: tokenResponse.expires_in,
    refreshToken: tokenResponse.refresh_token,
    scope: tokenResponse.scope,
    patient: tokenResponse.patient, // Patient context
    encounter: tokenResponse.encounter, // Encounter context
    fhirUser: tokenResponse.fhirUser // Practitioner context
  };
}
```

## SMART Scopes

### Clinical Scopes
```javascript
const SMART_SCOPES = {
  // Patient scopes
  PATIENT_READ: 'patient/*.read',
  PATIENT_WRITE: 'patient/*.write',
  PATIENT_ALL: 'patient/*.*',
  
  // Specific resource scopes
  PATIENT_PATIENT_READ: 'patient/Patient.read',
  PATIENT_OBSERVATION_READ: 'patient/Observation.read',
  PATIENT_CONDITION_READ: 'patient/Condition.read',
  PATIENT_MEDICATION_READ: 'patient/MedicationRequest.read',
  
  // User scopes (practitioner context)
  USER_READ: 'user/*.read',
  USER_WRITE: 'user/*.write',
  USER_ALL: 'user/*.*',
  
  // System scopes (backend services)
  SYSTEM_READ: 'system/*.read',
  SYSTEM_WRITE: 'system/*.write',
  SYSTEM_ALL: 'system/*.*',
  
  // Profile scopes
  OPENID: 'openid',
  FHIR_USER: 'fhirUser',
  PROFILE: 'profile',
  
  // Launch context
  LAUNCH: 'launch',
  LAUNCH_PATIENT: 'launch/patient',
  LAUNCH_ENCOUNTER: 'launch/encounter',
  
  // Offline access
  OFFLINE_ACCESS: 'offline_access'
};

function buildScopeString(resourceTypes, permissions, context = 'patient') {
  return resourceTypes.map(resource => 
    permissions.map(permission => `${context}/${resource}.${permission}`)
  ).flat().join(' ');
}

// Example usage
const scopes = [
  SMART_SCOPES.LAUNCH,
  SMART_SCOPES.OPENID,
  SMART_SCOPES.FHIR_USER,
  buildScopeString(['Patient', 'Observation', 'Condition'], ['read'], 'patient'),
  SMART_SCOPES.OFFLINE_ACCESS
].join(' ');
```

## FHIR Client with SMART Authentication

```javascript
class SMARTFHIRClient {
  constructor(baseUrl, tokenInfo) {
    this.baseUrl = baseUrl;
    this.tokenInfo = tokenInfo;
  }
  
  async request(method, path, data = null) {
    const url = `${this.baseUrl}/${path}`;
    const headers = {
      'Authorization': `${this.tokenInfo.tokenType} ${this.tokenInfo.accessToken}`,
      'Accept': 'application/fhir+json',
      'Content-Type': 'application/fhir+json'
    };
    
    const options = {
      method,
      headers
    };
    
    if (data) {
      options.body = JSON.stringify(data);
    }
    
    const response = await fetch(url, options);
    
    if (response.status === 401) {
      // Token expired, attempt refresh
      if (this.tokenInfo.refreshToken) {
        await this.refreshAccessToken();
        // Retry request with new token
        headers.Authorization = `${this.tokenInfo.tokenType} ${this.tokenInfo.accessToken}`;
        return fetch(url, { ...options, headers });
      } else {
        throw new Error('Authentication required');
      }
    }
    
    if (!response.ok) {
      throw new Error(`FHIR request failed: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  }
  
  async refreshAccessToken() {
    const refreshRequest = {
      grant_type: 'refresh_token',
      refresh_token: this.tokenInfo.refreshToken,
      client_id: this.clientId
    };
    
    const response = await fetch(this.tokenEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams(refreshRequest)
    });
    
    const newTokenInfo = await response.json();
    
    this.tokenInfo.accessToken = newTokenInfo.access_token;
    this.tokenInfo.expiresIn = newTokenInfo.expires_in;
    if (newTokenInfo.refresh_token) {
      this.tokenInfo.refreshToken = newTokenInfo.refresh_token;
    }
  }
  
  // FHIR operations
  async read(resourceType, id) {
    return this.request('GET', `${resourceType}/${id}`);
  }
  
  async search(resourceType, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const path = queryString ? `${resourceType}?${queryString}` : resourceType;
    return this.request('GET', path);
  }
  
  async create(resource) {
    return this.request('POST', resource.resourceType, resource);
  }
  
  async update(resource) {
    return this.request('PUT', `${resource.resourceType}/${resource.id}`, resource);
  }
  
  async delete(resourceType, id) {
    return this.request('DELETE', `${resourceType}/${id}`);
  }
  
  // Patient context operations
  async getPatientContext() {
    if (this.tokenInfo.patient) {
      return this.read('Patient', this.tokenInfo.patient);
    }
    throw new Error('No patient context available');
  }
  
  async getPatientObservations(params = {}) {
    if (this.tokenInfo.patient) {
      return this.search('Observation', {
        ...params,
        subject: `Patient/${this.tokenInfo.patient}`
      });
    }
    throw new Error('No patient context available');
  }
}
```

## Backend Services (System Scopes)

### Client Credentials Flow
```javascript
class SMARTBackendClient {
  constructor(config) {
    this.config = config;
    this.accessToken = null;
    this.tokenExpiry = null;
  }
  
  async authenticate() {
    const now = Math.floor(Date.now() / 1000);
    const exp = now + 300; // 5 minutes
    
    // Create JWT assertion
    const header = {
      alg: 'RS384',
      typ: 'JWT',
      kid: this.config.keyId
    };
    
    const payload = {
      iss: this.config.clientId,
      sub: this.config.clientId,
      aud: this.config.tokenEndpoint,
      exp: exp,
      iat: now,
      jti: generateUUID()
    };
    
    const assertion = await this.signJWT(header, payload);
    
    const tokenRequest = {
      grant_type: 'client_credentials',
      scope: this.config.scopes.join(' '),
      client_assertion_type: 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
      client_assertion: assertion
    };
    
    const response = await fetch(this.config.tokenEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams(tokenRequest)
    });
    
    const tokenResponse = await response.json();
    
    this.accessToken = tokenResponse.access_token;
    this.tokenExpiry = now + tokenResponse.expires_in;
    
    return tokenResponse;
  }
  
  async signJWT(header, payload) {
    // Implementation depends on your JWT library
    // Example with node-jsonwebtoken:
    const jwt = require('jsonwebtoken');
    return jwt.sign(payload, this.config.privateKey, {
      algorithm: 'RS384',
      keyid: this.config.keyId,
      header: header
    });
  }
  
  async ensureValidToken() {
    const now = Math.floor(Date.now() / 1000);
    if (!this.accessToken || now >= this.tokenExpiry - 60) {
      await this.authenticate();
    }
  }
  
  async request(method, path, data = null) {
    await this.ensureValidToken();
    
    const url = `${this.config.fhirBaseUrl}/${path}`;
    const headers = {
      'Authorization': `Bearer ${this.accessToken}`,
      'Accept': 'application/fhir+json'
    };
    
    if (data) {
      headers['Content-Type'] = 'application/fhir+json';
    }
    
    const response = await fetch(url, {
      method,
      headers,
      body: data ? JSON.stringify(data) : null
    });
    
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  }
}
```

## Security Considerations

### Token Storage
```javascript
class SecureTokenStorage {
  static store(tokenInfo, persistent = false) {
    const storage = persistent ? localStorage : sessionStorage;
    
    // Encrypt sensitive data before storage
    const encrypted = this.encrypt(JSON.stringify(tokenInfo));
    storage.setItem('smart_tokens', encrypted);
  }
  
  static retrieve() {
    const encrypted = sessionStorage.getItem('smart_tokens') || 
                     localStorage.getItem('smart_tokens');
    
    if (encrypted) {
      const decrypted = this.decrypt(encrypted);
      return JSON.parse(decrypted);
    }
    
    return null;
  }
  
  static clear() {
    sessionStorage.removeItem('smart_tokens');
    localStorage.removeItem('smart_tokens');
  }
  
  static encrypt(data) {
    // Implementation depends on your crypto library
    // Use Web Crypto API for browser environments
    return btoa(data); // Simplified - use proper encryption
  }
  
  static decrypt(encryptedData) {
    return atob(encryptedData); // Simplified - use proper decryption
  }
}
```

### CSRF Protection
```javascript
function validateState(receivedState) {
  const storedState = sessionStorage.getItem('smart_state');
  sessionStorage.removeItem('smart_state');
  
  if (!storedState || receivedState !== storedState) {
    throw new Error('Invalid state parameter - possible CSRF attack');
  }
}
```

## Testing SMART Applications

### Mock SMART Server
```javascript
class MockSMARTServer {
  constructor() {
    this.clients = new Map();
    this.tokens = new Map();
    this.patients = new Map();
  }
  
  registerClient(clientId, config) {
    this.clients.set(clientId, config);
  }
  
  handleAuthorizationRequest(params) {
    const clientId = params.get('client_id');
    const redirectUri = params.get('redirect_uri');
    const scope = params.get('scope');
    const state = params.get('state');
    
    // Validate client
    const client = this.clients.get(clientId);
    if (!client || !client.redirectUris.includes(redirectUri)) {
      throw new Error('Invalid client or redirect URI');
    }
    
    // Generate authorization code
    const code = generateSecureRandom(32);
    this.tokens.set(code, {
      clientId,
      redirectUri,
      scope,
      expiresAt: Date.now() + 600000, // 10 minutes
      codeChallenge: params.get('code_challenge')
    });
    
    // Redirect with code
    const redirectUrl = new URL(redirectUri);
    redirectUrl.searchParams.set('code', code);
    redirectUrl.searchParams.set('state', state);
    
    return redirectUrl.toString();
  }
  
  handleTokenRequest(body) {
    const code = body.get('code');
    const clientId = body.get('client_id');
    const codeVerifier = body.get('code_verifier');
    
    const authData = this.tokens.get(code);
    if (!authData || authData.expiresAt < Date.now()) {
      throw new Error('Invalid or expired authorization code');
    }
    
    // Validate PKCE
    if (authData.codeChallenge) {
      const challenge = generateCodeChallenge(codeVerifier);
      if (challenge !== authData.codeChallenge) {
        throw new Error('Invalid code verifier');
      }
    }
    
    // Generate access token
    const accessToken = generateSecureRandom(32);
    
    return {
      access_token: accessToken,
      token_type: 'Bearer',
      expires_in: 3600,
      scope: authData.scope,
      patient: 'example-patient-id'
    };
  }
}
```

## Integration Examples

### React SMART App
```jsx
import React, { useState, useEffect } from 'react';

function SMARTApp() {
  const [client, setClient] = useState(null);
  const [patient, setPatient] = useState(null);
  const [observations, setObservations] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    initializeSMART();
  }, []);
  
  async function initializeSMART() {
    try {
      // Check for authorization code in URL
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');
      
      if (code) {
        // Exchange code for token
        validateState(state);
        const smartConfig = await discoverSmartConfig(FHIR_BASE_URL);
        const tokenInfo = await exchangeCodeForToken(code, smartConfig, APP_CONFIG);
        
        // Initialize FHIR client
        const fhirClient = new SMARTFHIRClient(FHIR_BASE_URL, tokenInfo);
        setClient(fhirClient);
        
        // Load patient context
        const patientData = await fhirClient.getPatientContext();
        setPatient(patientData);
        
        // Load observations
        const obsData = await fhirClient.getPatientObservations({
          category: 'vital-signs',
          _sort: '-date'
        });
        setObservations(obsData.entry || []);
        
      } else {
        // Redirect to authorization
        const smartConfig = await discoverSmartConfig(FHIR_BASE_URL);
        const authUrl = buildAuthorizationUrl(smartConfig, APP_CONFIG);
        window.location.href = authUrl;
      }
      
    } catch (error) {
      console.error('SMART initialization failed:', error);
    } finally {
      setLoading(false);
    }
  }
  
  if (loading) {
    return <div>Loading...</div>;
  }
  
  return (
    <div>
      <h1>SMART on FHIR App</h1>
      {patient && (
        <div>
          <h2>Patient: {patient.name?.[0]?.given?.join(' ')} {patient.name?.[0]?.family}</h2>
          <p>DOB: {patient.birthDate}</p>
          <p>Gender: {patient.gender}</p>
        </div>
      )}
      
      <h3>Recent Vital Signs</h3>
      <ul>
        {observations.map((entry, index) => (
          <li key={index}>
            {entry.resource.code.coding[0].display}: {entry.resource.valueQuantity?.value} {entry.resource.valueQuantity?.unit}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default SMARTApp;
```

This reference provides comprehensive patterns for implementing SMART on FHIR applications across different scenarios and environments.
