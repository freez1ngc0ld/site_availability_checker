import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '../api.js';
import OtpInput from '../components/OtpInput';

export default function DeleteAccountPage() {
  const [step, setStep] = useState(1);
  const [otp, setOtp] = useState(new Array(6).fill(""));
  const [tempToken, setTempToken] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleRequest = async () => {
    setError('');
    try {
      const { data } = await authAPI.deleteAccountRequest();
      setTempToken(data.access_token);
      setStep(2);
    } catch (err) {
      setError(err.response?.data?.detail || 'The action is limited');
    }
  };

  const handleConfirm = async () => {
    setError('');
    try {
      await authAPI.deleteAccountConfirm(otp.join(''), tempToken);
      localStorage.clear();
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid 6-digits code');
    }
  };

  return (
    <div className="auth-screen">
      <div className="card-base auth-card" style={{ textAlign: 'center' }}>
        <h2 style={{ color: 'var(--status-error)', fontSize: '14px', letterSpacing: '0.05em', marginBottom: '1rem' }}>
          // DESTRUCTIVE ACTION
        </h2>
        
        {error && <div className="alert alert-error">{`> ${error}`}</div>}

        {step === 1 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <p style={{ color: 'var(--text-muted)', fontSize: '12px', lineHeight: '1.6' }}>
              Deleting your account will permanently destroy all configured host verification configurations.
            </p>
            <button 
              onClick={handleRequest} 
              className="btn-primary" 
              style={{ backgroundColor: 'var(--status-error)', color: '#ffffff' }}
            >
              Request deletion
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <p style={{ color: 'var(--text-muted)' }}>Enter the 6-digits token sent to your email:</p>
            <OtpInput value={otp} onChange={setOtp} />
            <button 
              onClick={handleConfirm} 
              className="btn-primary"
              style={{ backgroundColor: 'var(--status-error)', color: '#ffffff', marginTop: '1rem' }}
            >
              Confirm deletion
            </button>
          </div>
        )}
      </div>
    </div>
  );
}