import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function LogoutPage() {
  const navigate = useNavigate();
  useEffect(() => {
    localStorage.clear();
    navigate('/login');
  }, [navigate]);

  return (
    <div className="min-h-screen bg-black font-mono text-zinc-600 flex items-center justify-center text-xs">
      // TERMINATING_ACTIVE_SESSION...
    </div>
  );
}