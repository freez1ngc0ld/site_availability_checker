import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Header from './Header.jsx';
import { checkerAPI } from '../api.js';

const ITEMS_PER_PAGE = 15;

export default function MainPage() {
  const [checkers, setCheckers] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [logs, setLogs] = useState([]);
  const [newUrl, setNewUrl] = useState('');
  const [error, setError] = useState('');

  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [idToDelete, setIdToDelete] = useState(null);

  const navigate = useNavigate();

  const loadCheckers = async (targetPage = page, append = false) => {
    if (isLoading) return;
    setIsLoading(true);
    
    try {
      const limit = append ? ITEMS_PER_PAGE : targetPage * ITEMS_PER_PAGE;
      const offset = append ? (targetPage - 1) * ITEMS_PER_PAGE : 0;
      
      const { data } = await checkerAPI.getAll(limit, offset);
      
      if (append) {
        setCheckers(prev => {
          const prevIds = new Set(prev.map(c => c.id));
          const uniqueNew = data.filter(item => !prevIds.has(item.id));
          return [...prev, ...uniqueNew];
        });
        setHasMore(data.length === ITEMS_PER_PAGE);
      } else {
        setCheckers(data);
        setHasMore(data.length === targetPage * ITEMS_PER_PAGE);
      }

      if (data.length > 0 && !selectedId) {
        setSelectedId(data[0].id);
      }
    } catch (err) {
      if (err.response?.status === 401) navigate('/logout');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { 
    loadCheckers(1, false); 
  }, []);

  useEffect(() => {
    if (page > 1) {
      loadCheckers(page, true);
    }
  }, [page]);

  useEffect(() => {
    if (!selectedId) return;

    const fetchLogs = () => {
      checkerAPI.getLogs(selectedId)
        .then(({ data }) => setLogs(data))
        .catch(() => setLogs([]));
    };

    fetchLogs();

    const intervalId = setInterval(() => {
      fetchLogs();
      loadCheckers(page, false); 
    }, 30000);

    return () => clearInterval(intervalId);
  }, [selectedId, page]);

  const extractErrorMessage = (err, defaultMessage) => {
    const detail = err.response?.data?.detail;
    if (!detail) return defaultMessage;
    if (Array.isArray(detail)) return detail[0]?.msg || defaultMessage;
    if (typeof detail === 'string') return detail;
    return defaultMessage;
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const { data } = await checkerAPI.add(newUrl);
      setNewUrl('');
      setSelectedId(data.id);
      loadCheckers(page, false);
    } catch (err) {
      setError(extractErrorMessage(err, 'Error adding a site checker'));
    }
  };

  const triggerDeleteModal = (id) => {
    setIdToDelete(id);
    setIsModalOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!idToDelete) return;
    setError('');
    try {
      await checkerAPI.delete(idToDelete);
      const updatedCheckers = checkers.filter(c => c.id !== idToDelete);
      
      if (updatedCheckers.length === 0 && page > 1) {
        setPage(prev => prev - 1);
      } else {
        loadCheckers(page, false);
      }
      
      if (selectedId === idToDelete) {
        if (updatedCheckers.length > 0) {
          setSelectedId(updatedCheckers[0].id);
        } else {
          setSelectedId(null);
          setLogs([]);
        }
      }
      setIsModalOpen(false);
      setIdToDelete(null);
    } catch (err) {
      setError(extractErrorMessage(err, 'Error with deleting site checker'));
      setIsModalOpen(false);
      setIdToDelete(null);
    }
  };

  const handleScroll = (e) => {
    const { scrollTop, clientHeight, scrollHeight } = e.target;
    if (scrollHeight - scrollTop <= clientHeight + 15) {
      if (hasMore && !isLoading) {
        setPage(prev => prev + 1);
      }
    }
  };

  const formatToLocalTime = (dateStr) => {
    if (!dateStr) return '---';
    let isoStr = dateStr;
    if (!isoStr.endsWith('Z') && !isoStr.includes('+')) {
      isoStr = isoStr.replace(' ', 'T') + 'Z';
    }
    return new Date(isoStr).toLocaleTimeString();
  };

  const activeChecker = checkers.find(c => c.id === selectedId);
  const totalLogs = logs.length;
  const successLogs = logs.filter(l => l.status_code >= 200 && l.status_code < 300).length;
  const uptime = totalLogs ? Math.round((successLogs / totalLogs) * 100) : 100;
  const lastLog = logs[logs.length - 1];

  const getMostFrequentStatusCode = (logArray) => {
    if (!logArray.length) return '---';
    const frequencies = {};
    let mostFrequentCode = logArray[0].status_code;
    let maxCount = 0;

    for (const log of logArray) {
      const code = log.status_code;
      frequencies[code] = (frequencies[code] || 0) + 1;
      if (frequencies[code] > maxCount) {
        maxCount = frequencies[code];
        mostFrequentCode = code;
      }
    }
    return mostFrequentCode;
  };

  const mostFrequentStatus = getMostFrequentStatusCode(logs);

  const validPingLogs = logs.filter(log => log.status_code !== 0);
  const avgResponseTime = validPingLogs.length
    ? Math.round(validPingLogs.reduce((sum, log) => sum + log.response_time_ms, 0) / validPingLogs.length)
    : '---';

  return (
    <div style={{ paddingBottom: '3rem' }}>
      <Header/>

      <div className="container main-layout" style={{ alignItems: 'stretch' }}>

        <div className="card-base" style={{ 
          height: 'calc(100vh - 150px)', 
          minHeight: '450px',            
          maxHeight: '750px',            
          display: 'flex', 
          flexDirection: 'column', 
          boxSizing: 'border-box'
        }}>
          <h3 className="card-title" style={{ flexShrink: 0 }}>Site checkers</h3>
          
          <form onSubmit={handleAdd} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flexShrink: 0 }}>
            <input
              type="url"
              placeholder="https://example.com"
              required
              value={newUrl}
              onChange={(e) => setNewUrl(e.target.value)}
              className="input-field"
              style={{ padding: '0.5rem', fontSize: '12px' }}
            />
            <button type="submit" className="btn-secondary" style={{ flexShrink: 0 }}>+ Add site checker</button>
          </form>
          
          {error && <div className="alert alert-error" style={{ marginTop: '0.5rem', padding: '0.5rem', flexShrink: 0 }}>{error}</div>}

          <div 
            className="nodes-list" 
            onScroll={handleScroll}
            style={{ 
              flex: 1, 
              overflowY: 'auto', 
              minHeight: 0, 
              marginTop: '1rem', 
              paddingRight: '4px' 
            }}
          >
            {checkers.map(c => (
              <div
                key={c.id}
                onClick={() => setSelectedId(c.id)}
                className={`node-item ${c.id === selectedId ? 'active' : ''}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '0.5rem 0.75rem',
                  minHeight: '36px',
                  boxSizing: 'border-box',
                  cursor: 'pointer'
                }}
              >
                {c.site_url.replace(/^https?:\/\//, '')}
              </div>
            ))}

            {isLoading && (
              <div style={{ 
                textAlign: 'center', 
                padding: '0.5rem', 
                color: 'var(--text-muted)', 
                fontSize: '11px',
                fontFamily: 'monospace'
              }}>
                [ LOADING_MORE... ]
              </div>
            )}
          </div>
        </div>

        <div>
          {activeChecker ? (
            <>
              <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
                <h2>Availability checking {activeChecker.site_url.replace(/^https?:\/\//, '')}</h2>
                
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.75rem', marginTop: '6px' }}>
                  <p style={{ color: 'var(--text-muted)', fontSize: '11px', margin: 0 }}>
                    Last update: {lastLog ? formatToLocalTime(lastLog.created_at) : '--:--:--'}
                  </p>
                  <span style={{ color: 'var(--border-color)', fontSize: '11px' }}>|</span>
                  <button 
                    type="button" 
                    onClick={() => triggerDeleteModal(activeChecker.id)}
                    style={{ 
                      background: 'none', 
                      border: 'none', 
                      color: 'var(--status-error)', 
                      fontSize: '11px', 
                      fontFamily: 'monospace', 
                      cursor: 'pointer', 
                      padding: 0 
                    }}
                  >
                    [ DELETE_CHECKER ]
                  </button>
                </div>
              </div>

              <div className="metrics-grid">
                <div className="card-base metric-card">
                  <span className={`metric-value ${typeof mostFrequentStatus === 'number' && mostFrequentStatus >= 200 && mostFrequentStatus < 300 ? 'success' : 'error'}`}>
                    {mostFrequentStatus}
                  </span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '11px', marginTop: '4px' }}>Status code (frequent)</span>
                </div>

                <div className="card-base metric-card">
                  <span className="metric-value info">
                    {avgResponseTime}{typeof avgResponseTime === 'number' ? 'ms' : ''}
                  </span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '11px', marginTop: '4px' }}>Mean response time</span>
                </div>

                <div className="card-base metric-card">
                  <span className="metric-value warn">{uptime}%</span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '11px', marginTop: '4px' }}>Uptime (24h)</span>
                </div>

                <div className="card-base metric-card">
                  <span className="metric-value time">
                    {lastLog ? formatToLocalTime(lastLog.created_at) : '---'}
                  </span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '11px', marginTop: '4px' }}>Last ping</span>
                </div>
              </div>

              <div className="card-base">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: 'var(--status-success)' }}></span>
                  <div>
                    <h4 style={{ fontSize: '14px' }}>Ping journal</h4>
                    <p style={{ color: 'var(--text-muted)', fontSize: '11px' }}>{activeChecker.site_url}</p>
                  </div>
                </div>

                <h4 className="card-title" style={{ marginTop: '1.5rem' }}>Ping history</h4>
                
                <div className="log-dots-container">
                  {logs.length > 0 ? (
                    logs.map((log) => (
                      <div
                        key={log.id}
                        title={`Status: ${log.status_code}\nTime: ${formatToLocalTime(log.created_at)}\nPing: ${log.response_time_ms} мс`}
                        className={`dot ${log.status_code >= 200 && log.status_code < 300 ? 'success' : 'error'}`}
                      />
                    ))
                  ) : (
                    <span style={{ color: 'var(--text-muted)', margin: 'auto', fontSize: '12px' }}>Journal is empty</span>
                  )}
                </div>

                <div style={{ display: 'flex', gap: '1.5rem', fontSize: '11px', color: 'var(--text-muted)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <span className="dot success" style={{ width: '8px', height: '8px', cursor: 'default' }}></span> Available
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <span className="dot error" style={{ width: '8px', height: '8px', cursor: 'default' }}></span> Error
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="card-base" style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              [ JOURNAL IS EMPTY. ADD THE FIRST ADDRESS TO THE PANEL ON THE LEFT ]
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
              // DELETE_CHECKER_CONFIRMATION
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '12px', lineHeight: '1.6', marginBottom: '2rem' }}>
              You are about to permanently delete this node from the core-monitor tracking system. All accumulated logs will be erased from the database.
            </p>
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
              <button 
                type="button" 
                onClick={() => { setIsModalOpen(false); setIdToDelete(null); }} 
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
                DELETE
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}