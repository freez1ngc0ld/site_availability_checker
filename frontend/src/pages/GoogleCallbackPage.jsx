import React, { useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { authAPI } from '../api';

export default function GoogleCallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const loginDispatched = useRef(false);

  useEffect(() => {
    const code = searchParams.get('code');
    
    if (code) {
      if (loginDispatched.current) return;
      loginDispatched.current = true;

      authAPI.googleLogin(code)
        .then(({ data }) => {
          localStorage.setItem('token', data.access_token);
          navigate('/dashboard');
        })
        .catch((err) => {
          console.error("Google Auth Error:", err);
          navigate('/login');
        });
    } else {
      navigate('/login');
    }
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen bg-black font-mono text-zinc-500 flex items-center justify-center">
      <div className="animate-pulse tracking-widest text-xs">
        // EXTRACTING_GOOGLE_SECURE_TOKEN...
      </div>
    </div>
  );
}