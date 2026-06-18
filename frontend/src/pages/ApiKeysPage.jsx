import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Header from './Header';
import { apiKeyAPI } from '../api';

const ITEMS_PER_PAGE = 15;

function KeyRow({ apiKey, onDelete }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(apiKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (err) {
      console.error('Failed to copy', err);
    }
  };

  return (
    <div 
      className="node-item" 
      style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        cursor: 'default',
        padding: '0.75rem 0.5rem', 
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        height: 'auto',
        margin: 0,
        gap: '1.5rem'
      }}
    >
      <code style={{ color: 'var(--text-main)', fontFamily: 'monospace' }}>
        {apiKey}
      </code>
      <div style={{ display: 'flex', gap: '0.5rem', flexShrink: 0 }}>
        <button 
          onClick={handleCopy} 
          className="btn-secondary"
          style={{ 
            padding: '0.4rem 0.6rem', 
            fontSize: '11px',
            width: '65px',
            textAlign: 'center',
            backgroundColor: copied ? 'var(--status-success)' : 'var(--border-color)',
            color: copied ? 'var(--accent-text)' : 'var(--text-main)'
          }}
        >
          {copied ? 'COPIED' : 'COPY'}
        </button>
        <button 
          onClick={() => onDelete(apiKey)} 
          className="btn-secondary"
          style={{ padding: '0.4rem 0.6rem', fontSize: '11px', width: '75px' }}
        >
          REVOKE
        </button>
      </div>
    </div>
  );
}

export default function ApiKeysPage() {
  const [keys, setKeys] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [newKey, setNewKey] = useState('');

  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialLoading, setIsInitialLoading] = useState(true);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [keyToDelete, setKeyToDelete] = useState(null);

  const loadKeys = async (targetPage = page, append = false) => {
    if (isLoading) return;
    setIsLoading(true);
    
    try {
      const limit = append ? ITEMS_PER_PAGE : targetPage * ITEMS_PER_PAGE;
      const offset = append ? (targetPage - 1) * ITEMS_PER_PAGE : 0;
      
      const { data } = await apiKeyAPI.getAll({ limit, offset });
      
      if (append) {
        setKeys(prev => {
          const prevKeys = new Set(prev.map(k => k.key));
          const uniqueNew = data.filter(item => !prevKeys.has(item.key));
          return [...prev, ...uniqueNew];
        });
        setHasMore(data.length === ITEMS_PER_PAGE);
      } else {
        setKeys(data);
        setHasMore(data.length === targetPage * ITEMS_PER_PAGE);
      }
    } catch (err) {
      setError('ERROR_FETCHING_KEYS: Access denied or server offline');
    } finally {
      setIsLoading(false);
      setIsInitialLoading(false);
    }
  };

  useEffect(() => {
    loadKeys(1, false);
  }, []);

  useEffect(() => {
    if (page > 1) {
      loadKeys(page, true);
    }
  }, [page]);

  const handleScroll = (e) => {
    const { scrollTop, clientHeight, scrollHeight } = e.target;
    if (scrollHeight - Math.ceil(scrollTop) - clientHeight <= 40) {
      if (hasMore && !isLoading) {
        setPage(prev => prev + 1);
      }
    }
  };

  const handleCreateKey = async () => {
    setError('');
    setSuccess('');
    setNewKey('');
    try {
      const { data } = await apiKeyAPI.create();
      setNewKey(data.key);
      setSuccess('API_KEY_CREATED: The new API key has been successfully deployed');
      setPage(1);
      loadKeys(1, false);
    } catch (err) {
      setError('ERROR_CREATION_FAILED: Failed to generate a token API key');
    }
  };

  const triggerDeleteModal = (keyString) => {
    setKeyToDelete(keyString);
    setIsModalOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!keyToDelete) return;
    setError('');
    try {
      await apiKeyAPI.delete(keyToDelete);
      if (newKey === keyToDelete) {
        setNewKey('');
        setSuccess('');
      }
      
      const updatedKeys = keys.filter((k) => k.key !== keyToDelete);
      setKeys(updatedKeys);

      if (updatedKeys.length === 0 && page > 1) {
        setPage(prev => prev - 1);
      } else {
        loadKeys(page, false);
      }
      
      setIsModalOpen(false);
      setKeyToDelete(null);
    } catch (err) {
      setError("ERROR_DELETION_FAILED: Couldn't revoke the API key");
      setIsModalOpen(false);
      setKeyToDelete(null);
    }
  };

  return (
    <>
    <Header/>
    <div className="container" style={{ marginTop: '2rem', marginBottom: '2rem' }}>
      
      <div className="card-base" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div className="card-title">// ACCESS_TOKEN_MANAGER</div>
          <Link 
            to="/api/docs" 
            target="_blank" 
            rel="noreferrer"
            style={{
              fontFamily: 'monospace',
              fontSize: '11px',
              color: 'var(--accent-color)',
              textDecoration: 'none',
              padding: '0.2rem 0.5rem',
              border: '1px dashed var(--accent-color)',
              borderRadius: '2px',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'opacity 0.2s'
            }}
            onMouseEnter={(e) => e.target.style.opacity = '0.8'}
            onMouseLeave={(e) => e.target.style.opacity = '1'}
          >
            <span>API_DOCS</span>
            <span style={{ fontSize: '10px' }}>↗</span>
          </Link>
        </div>
        <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
          Management of public authorization keys for external subsystems and the Checker API.
        </p>

        {error && <div className="alert alert-error">// {error}</div>}
        {success && <div className="alert alert-success">// {success}</div>}

        <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 300px' }}>
            <p style={{ fontWeight: 'bold', marginBottom: '0.25rem' }}>Generate Public API Key</p>
            <p style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
              The key is passed as a string in the query parameters of authorized endpoints (?api_key=...).
            </p>
          </div>
          <div style={{ width: '180px' }}>
            <button onClick={handleCreateKey} className="btn-primary">
              GENERATE_KEY
            </button>
          </div>
        </div>

        {newKey && (
          <div style={{ marginTop: '1.5rem' }}>
            <p style={{ color: 'var(--status-success)', fontSize: '11px', marginBottom: '0.5rem' }}>
              // COPY KEY:
            </p>
            <input 
              type="text" 
              className="input-field" 
              value={newKey} 
              readOnly 
              onClick={(e) => e.target.select()}
              style={{ color: 'var(--accent-color)', fontWeight: 'bold', letterSpacing: '0.05em' }}
            />
          </div>
        )}
      </div>

      <div className="card-base">
        <div className="card-title">// ACTIVE_KEYS_POOL</div>

        {isInitialLoading ? (
          <p style={{ color: 'var(--text-muted)' }}>Scanning active tokens database...</p>
        ) : keys.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem 0' }}>
            There are no active keys in the pool. Generate a token above.
          </p>
        ) : (
          <div 
            className="nodes-list" 
            onScroll={handleScroll}
            style={{ 
              maxHeight: '400px', 
              minHeight: 0, 
              marginTop: '1rem', 
              paddingRight: '4px',
              display: 'flex',
              flexDirection: 'column'
            }}
          >
            {keys.map((k) => (
              <KeyRow 
                key={k.key} 
                apiKey={k.key} 
                onDelete={triggerDeleteModal} 
              />
            ))}
            
            {isLoading && (
              <div style={{ 
                textAlign: 'center', 
                padding: '0.75rem 0', 
                color: 'var(--text-muted)', 
                fontSize: '11px',
                fontFamily: 'monospace',
                flexShrink: 0
              }}>
                [ LOADING_MORE... ]
              </div>
            )}
          </div>
        )}
      </div>
    </div>

    {isModalOpen && (
      <div style={{
        position: 'fixed',
        top: 0, left: 0, right: 0, bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        backdropFilter: 'blur(4px)',
        WebkitBackdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999
      }}>
        <div className="card-base" style={{ maxWidth: '420px', width: '90%', padding: '2rem', textAlign: 'center' }}>
          <h3 style={{ color: 'var(--status-error)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '1rem' }}>
            // REVOKE_TOKEN_CONFIRMATION
          </h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '12px', lineHeight: '1.6', marginBottom: '2rem' }}>
            You are about to revoke this API key. All external integrations, scripts, and Checker APIs that use this token will instantly lose access.
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
            <button 
              type="button" 
              onClick={() => { setIsModalOpen(false); setKeyToDelete(null); }} 
              className="btn-secondary"
              style={{ flex: 1, margin: 0 }}
            >
              CANCEL
            </button>
            <button 
              type="button" 
              onClick={handleConfirmDelete} 
              className="btn-primary"
              style={{ 
                flex: 1, 
                margin: 0, 
                backgroundColor: 'var(--status-error)', 
                borderColor: 'var(--status-error)',
                color: '#000'
              }}
            >
              REVOKE
            </button>
          </div>
        </div>
      </div>
    )}
    </>
  );
}