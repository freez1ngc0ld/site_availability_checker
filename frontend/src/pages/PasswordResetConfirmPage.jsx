import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { authAPI } from '../api';

export default function PasswordResetConfirmPage() {
  const { token } = useParams();
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleConfirm = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await authAPI.resetPasswordConfirm(token, password);
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update credentials');
    }
  };

  return (
    <div className="auth-screen">
      <div className="card-base auth-card">
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ letterSpacing: '0.1em', textTransform: 'uppercase' }}>
            //NEW_CREDENTIALS
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '11px', marginTop: '4px', lineHeight: '1.5' }}>
            Establish new very hard password for entry.
          </p>
        </div>

        {error && <div className="alert alert-error">{`> ${error}`}</div>}

        <form onSubmit={handleConfirm} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <input
            type="password"
            placeholder="NEW_CRYPT_PASSWORD"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input-field"
          />
          <button type="submit" className="btn-primary">
            CONFIRM_RESET
          </button>
        </form>
      </div>
    </div>
  );
}