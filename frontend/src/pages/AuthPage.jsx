import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../api.js';

export default function AuthPage({ isLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); setMessage('');
    try {
      if (isLogin) {
        const { data } = await authAPI.login(email, password);
        localStorage.setItem('token', data.access_token);
        navigate('/dashboard');
      } else {
        const { data } = await authAPI.register(email, password);
        setMessage(data.message || 'The verification link has been sent!');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication error');
    }
  };

const handleGoogleLogin = async () => {
  setError(''); 
  setMessage('');
  try {
    const { data } = await authAPI.getGoogleUrl();
    if (data && data.url) {
      window.location.href = data.url;
    } else {
      setError('Critical error: The server did not provide a login URL');
    }
  } catch (err) {
    setError(err.response?.data?.detail || 'Failed to initialize Google Auth');
  }
};
  return (
    <div className="auth-screen">
      <div className="card-base auth-card">
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ letterSpacing: '0.1em', textTransform: 'uppercase' }}>
            {isLogin ? '// SECURE_LOGIN' : '// REGISTER_ID'}
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '11px', marginTop: '4px' }}>
            // SITE_AVAILABILITY_CHECKER
          </p>
        </div>

        {error && <div className="alert alert-error">{`> ${error}`}</div>}
        {message && <div className="alert alert-success">{`> ${message}`}</div>}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <input
            type="email"
            placeholder="USER_EMAIL"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="input-field"
          />
          <input
            type="password"
            placeholder="CRYPT_PASSWORD"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input-field"
          />

          {isLogin && (
            <div style={{ textAlign: 'right' }}>
              <Link to="/reset-password" style={{ fontSize: '11px', color: 'var(--text-muted)', textDecoration: 'none' }}>
                Forgot password?
              </Link>
            </div>
          )}

          <button type="submit" className="btn-primary" style={{ marginTop: '0.5rem' }}>
            {isLogin ? 'Log in' : 'Sign up'}
          </button>
        </form>

          <>
            <div className="google-divider">OR </div>
            <button type="button" onClick={handleGoogleLogin} className="btn-google">
              <svg className="google-icon" viewBox="0 0 24 24">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              Log in via Google
            </button>
          </>

        <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1rem', marginTop: '1.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '12px' }}>
          {isLogin ? (
            <>No account? <Link to="/registration" style={{ color: 'var(--text-main)' }}>CREATE_ID</Link></>
          ) : (
            <>Already have an account? <Link to="/login" style={{ color: 'var(--text-main)' }}>SIGN_IN</Link></>
          )}
        </div>
      </div>
    </div>
  );
}