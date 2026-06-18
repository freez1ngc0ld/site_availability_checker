import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { authAPI } from '../api';

export default function PasswordResetRequestPage() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleRequest = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    try {
      const { data } = await authAPI.resetPasswordRequest(email);
      setMessage(data.message || 'Access token link generated.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error processing request');
    }
  };

  return (
    <div className="auth-screen">
      <div className="card-base auth-card">
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ letterSpacing: '0.1em', textTransform: 'uppercase' }}>
            //RESET_PASSWORD
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '11px', marginTop: '4px', lineHeight: '1.5' }}>
            Provide account email node to generate secure access state reset link.
          </p>
        </div>

        {error && <div className="alert alert-error">{`> ${error}`}</div>}
        {message && <div className="alert alert-success">{`> ${message}`}</div>}

        <form onSubmit={handleRequest} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <input
            type="email"
            placeholder="mycoolemail@example.com"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="input-field"
            style={{ trackingWider: 'true' }}
          />
          <button type="submit" className="btn-primary">
            GENERATE_LINK
          </button>
        </form>

        <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1rem', marginTop: '1.5rem', textAlign: 'center' }}>
          <Link 
            to="/login" 
            style={{ color: 'var(--text-muted)', textDecoration: 'none', fontSize: '11px', letterSpacing: '0.05em', transition: 'color 0.2s' }}
            onMouseEnter={(e) => e.target.style.color = 'var(--text-main)'}
            onMouseLeave={(e) => e.target.style.color = 'var(--text-muted)'}
          >
            [ BACK_TO_LOGIN ]
          </Link>
        </div>
      </div>
    </div>
  );
}