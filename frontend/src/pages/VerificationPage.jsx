import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { authAPI } from '../api';

export default function VerificationPage() {
  const { token } = useParams();
  const [status, setStatus] = useState('PROCESSING_VERIFICATION...');
  const navigate = useNavigate();

  useEffect(() => {
    authAPI.verificate(token)
      .then(({ data }) => {
        localStorage.setItem('token', data.access_token);
        setStatus('VERIFIED. REDIRECTING...');
        setTimeout(() => navigate('/dashboard'), 1500);
      })
      .catch((err) => {
        setStatus(`ERROR: ${err.response?.data?.detail || 'Invalid or expired token.'}`);
      });
  }, [token, navigate]);

  return (
    <div className="min-h-screen bg-black font-mono text-white flex items-center justify-center">
      <div className="tracking-widest text-sm border border-zinc-900 p-6 bg-zinc-950">{`> ${status}`}</div>
    </div>
  );
}