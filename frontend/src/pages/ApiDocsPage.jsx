import React, { useState, useEffect } from 'react';
import Header from './Header';

function CopyableBlock({ value, rows, isResponse = false, type = 'textarea' }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (err) {
      console.error('Copy failed', err);
    }
  };

  const isInput = type === 'input';

  return (
    <div style={{ 
      display: 'flex', 
      gap: '0.5rem', 
      alignItems: isInput ? 'stretch' : 'flex-start' 
    }}>
      {isInput ? (
        <input 
          type="text" 
          className="input-field" 
          readOnly 
          value={value} 
          style={{ color: 'var(--text-muted)', margin: 0 }} 
        />
      ) : (
        <textarea 
          className="input-field" 
          rows={rows}
          readOnly
          value={value}
          style={{ 
            resize: 'none', 
            backgroundColor: 'rgba(0,0,0,0.2)', 
            color: isResponse ? 'var(--text-muted)' : 'var(--text-main)',
            margin: 0
          }}
        />
      )}
      <button 
        onClick={handleCopy} 
        className="btn-secondary"
        style={{ 
          width: '75px', 
          flexShrink: 0, 
          fontSize: '11px', 
          padding: isInput ? '0' : '0.75rem 0',
          textAlign: 'center',
          borderColor: copied ? 'var(--status-success)' : 'var(--border-color)',
          color: copied ? 'var(--status-success)' : 'var(--text-main)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        {copied ? 'COPIED' : 'COPY'}
      </button>
    </div>
  );
}

export default function ApiDocsPage() {
  const [spec, setSpec] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const BASE_URL = 'http://localhost:8000/api';

  useEffect(() => {
    const fetchOpenApiSpec = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${BASE_URL}/openapi.json`);
        if (!response.ok) throw new Error('ERR_SPEC_FETCH_FAILED');
        const data = await response.json();
        setSpec(data);
      } catch (err) {
        setError(`ERROR_FETCHING_OPENAPI: Failed to load openapi.json. Make sure that the backend is running on ${BASE_URL} and that CORS is configured.`);
      } finally {
        setLoading(false);
      }
    };

    fetchOpenApiSpec();
  }, []);

  const buildJsonExample = (schema, components) => {
    if (!schema) return null;

    if (schema.$ref) {
      const schemaName = schema.$ref.split('/').pop();
      const actualSchema = components?.schemas?.[schemaName];
      return buildJsonExample(actualSchema, components);
    }

    if (schema.type === 'array') {
      return [buildJsonExample(schema.items, components)];
    }

    if (schema.type === 'object' || schema.properties) {
      const obj = {};
      for (const [key, value] of Object.entries(schema.properties || {})) {
        if (value.$ref) {
          obj[key] = buildJsonExample(value, components);
        } else if (value.type === 'array') {
          obj[key] = [buildJsonExample(value.items, components)];
        } else {
          if (value.example !== undefined) obj[key] = value.example;
          else if (value.type === 'integer' || value.type === 'number') obj[key] = 0;
          else if (value.type === 'boolean') obj[key] = false;
          else obj[key] = "string";
        }
      }
      return obj;
    }

    return "string";
  };

  if (loading) {
    return (
      <div className="container" style={{ marginTop: '2rem' }}>
        <p style={{ color: 'var(--text-muted)' }}>Parsing remote openapi.json specification...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container" style={{ marginTop: '2rem' }}>
        <div className="alert alert-error">// {error}</div>
      </div>
    );
  }

  return (
    <>
    <Header/>
    <div className="container" style={{ marginTop: '2rem', marginBottom: '2rem' }}>

      <div className="card-base" style={{ marginBottom: '2rem' }}>
        <div className="card-title">// {spec?.info?.title || 'PUBLIC_API_SPECIFICATION'}</div>
        <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
          Specification version: {spec?.info?.version || '1.0.0'}. Automatic generation of an interface based on FastAPI endpoints.
        </p>

        <p style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>Request authentication</p>
        <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>
          All public handles require the mandatory transmission of an access token. Pass it as a query parameter <code style={{ color: 'var(--accent-color)' }}>api_key</code>.
        </p>

        <CopyableBlock value={`${BASE_URL}/checkers?api_key=YOUR_API_KEY`} type="input" />
      </div>

      <div className="card-title" style={{ marginBottom: '1rem', fontSize: '12px' }}>// AVAILABLE_ENDPOINTS</div>

      {spec?.paths && Object.entries(spec.paths).map(([path, methods]) => (
        Object.entries(methods).map(([method, methodInfo]) => {
          if (path.includes('openapi.json')) return null;

          const queryParams = methodInfo.parameters?.filter(p => p.in === 'query') || [];
          const pathParams = methodInfo.parameters?.filter(p => p.in === 'path') || [];
          
          let queryChunks = queryParams.map(p => `${p.name}=your_${p.name}`).join('&');
          if (!queryChunks.includes('api_key')) {
            queryChunks = queryChunks ? `api_key=secret_token_here&${queryChunks}` : 'api_key=secret_token_here';
          }
          const displayQuery = queryChunks ? `?${queryChunks}` : '';
          const curlUrl = `${BASE_URL}${path}${displayQuery}`;
          const curlExample = `curl -X '${method.toUpperCase()}' \\\n  '${curlUrl}' \\\n  -H 'accept: application/json'`;

          const successResponse = methodInfo.responses?.['200'] || methodInfo.responses?.['201'];
          const responseSchema = successResponse?.content?.['application/json']?.schema;
          const jsonExample = responseSchema ? buildJsonExample(responseSchema, spec.components) : null;
          const totalRowsInResponse = jsonExample ? JSON.stringify(jsonExample, null, 2).split('\n').length : 4;

          let methodColor = 'var(--status-success)';
          if (method === 'post') methodColor = 'var(--accent-color)';
          if (method === 'delete') methodColor = 'var(--status-error)';

          return (
            <div className="card-base" key={`${path}-${method}`} style={{ marginBottom: '1.5rem' }}>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                <span style={{ color: methodColor, fontWeight: 'bold', textTransform: 'uppercase' }}>{method}</span>
                <span style={{ fontWeight: 'bold', fontSize: '14px' }}>{path}</span>
              </div>
              
              {methodInfo.summary && (
                <p style={{ color: 'var(--text-main)', marginBottom: '0.5rem', fontSize: '13px' }}>
                  {methodInfo.summary}
                </p>
              )}
              {methodInfo.description && (
                <p style={{ color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
                  {methodInfo.description}
                </p>
              )}

              {pathParams.length > 0 && (
                <div style={{ marginBottom: '1rem' }}>
                  <div className="card-title" style={{ fontSize: '10px', marginBottom: '0.5rem' }}>Path parameters:</div>
                  <ul style={{ listStyleType: 'none', paddingLeft: 0 }}>
                    {pathParams.map(p => (
                      <li key={p.name} style={{ marginBottom: '0.25rem' }}>
                        <code style={{ color: 'var(--accent-color)' }}>{p.name}</code>{' '}
                        {p.required && <span style={{ color: 'var(--status-error)' }}>(required)</span>}{' '}
                        <span style={{ color: 'var(--text-muted)' }}>— {p.schema?.type || 'string'}. {p.description || ''}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div style={{ marginBottom: '1.25rem' }}>
                <div className="card-title" style={{ fontSize: '10px', marginBottom: '0.5rem' }}>Query parameters:</div>
                <ul style={{ listStyleType: 'none', paddingLeft: 0, display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  <li>
                    <code style={{ color: 'var(--accent-color)' }}>api_key</code> <span style={{ color: 'var(--status-error)' }}>(required)</span> 
                    <span style={{ color: 'var(--text-muted)' }}> — a secret access token for the public node.</span>
                  </li>
                  {queryParams.filter(p => p.name !== 'api_key').map(p => (
                    <li key={p.name}>
                      <code style={{ color: 'var(--accent-color)' }}>{p.name}</code>{' '}
                      {p.required ? <span style={{ color: 'var(--status-error)' }}>(required)</span> : <span style={{ color: 'var(--text-muted)' }}>(optional)</span>}{' '}
                      <span style={{ color: 'var(--text-muted)' }}> — {p.description || `${p.schema?.type || 'string'}`}.</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="card-title" style={{ fontSize: '10px', marginBottom: '0.5rem' }}>Example of a call (cURL):</div>
              <div style={{ marginBottom: '1.25rem' }}>
                <CopyableBlock value={curlExample} rows={3} type="textarea" />
              </div>

              {jsonExample && (
                <>
                  <div className="card-title" style={{ fontSize: '10px', marginBottom: '0.5rem' }}>RESPONSE_200 (Application/JSON):</div>
                  <CopyableBlock value={JSON.stringify(jsonExample, null, 2)} rows={totalRowsInResponse} isResponse={true} type="textarea" />
                </>
              )}
            </div>
          );
        })
      ))}

    </div>
    </>
  );
}