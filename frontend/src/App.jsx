import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

import { ProtectedRoute } from './components/ProtectedRoute';

import AuthPage from './pages/AuthPage';
import LogoutPage from './pages/LogoutPage';
import PasswordResetRequestPage from './pages/PasswordResetRequestPage';
import PasswordResetConfirmPage from './pages/PasswordResetConfirmPage';
import VerificationPage from './pages/VerificationPage';
import DeleteAccountPage from './pages/DeleteAccountPage';
import GoogleCallbackPage from './pages/GoogleCallbackPage';
import ApiDocsPage from './pages/ApiDocsPage';
import ApiKeysPage from './pages/ApiKeysPage';

import MainPage from './pages/MainPage';

const RedirectPage = () => {
  return (
    <div className="min-h-screen bg-black font-mono text-zinc-500 flex items-center justify-center text-xs">
      {`> FORWARDING_TO_EXTERNAL_NODE...`}
    </div>
  );
};

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              <MainPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/delete-account" 
          element={
            <ProtectedRoute>
              <DeleteAccountPage />
            </ProtectedRoute>
          } 
        />

        <Route path="/login" element={<AuthPage isLogin={true} />} />
        <Route path="/logout" element={<LogoutPage />} />
        <Route path="/registration" element={<AuthPage isLogin={false} />} />
        <Route path="/reset-password" element={<PasswordResetRequestPage />} />

        <Route path="/api" element={<ApiKeysPage />} />
        <Route path="/api/docs" element={<ApiDocsPage />} />

        <Route path="/v/:token" element={<VerificationPage />} />
        <Route path="/r/:token" element={<PasswordResetConfirmPage />} />

        <Route path="/auth/google" element={<GoogleCallbackPage />} />

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
