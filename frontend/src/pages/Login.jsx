import React, { useState } from 'react';

export default function Login({ onLogin }) {
  const [email, setEmail] = useState('gauri@webtrace.ai');
  const [password, setPassword] = useState('password123');
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    onLogin();
  };

  return (
    <div style={{
      width: '100vw',
      height: '100vh',
      backgroundColor: '#090e1a',
      color: '#e8f0fc',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      boxSizing: 'border-box',
      margin: 0,
      padding: '20px'
    }}>
      <div style={{
        backgroundColor: '#0d1222',
        border: '1px solid #1a2639',
        borderRadius: '16px',
        padding: '36px',
        width: '100%',
        maxWidth: '420px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)'
      }}>
        {/* Header Branding */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '28px' }}>
          <div style={{
            backgroundColor: '#2563eb',
            width: '40px',
            height: '40px',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: '20px',
            boxShadow: '0 10px 15px -3px rgba(37, 99, 235, 0.4)'
          }}>
            🤖
          </div>
          <div>
            <h1 style={{ fontSize: '18px', fontWeight: 'bold', margin: 0, color: '#fff', letterSpacing: '0.5px' }}>WebTrace</h1>
            <p style={{ fontSize: '10px', color: '#64748b', margin: '2px 0 0 0', letterSpacing: '1px', textTransform: 'uppercase' }}>AI QA ENGINEER LOGIN</p>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Email Input */}
          <div style={{ marginBottom: '18px' }}>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: '600', color: '#94a3b8', marginBottom: '6px' }}>
              Work Email
            </label>
            <input 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{
                width: '100%',
                backgroundColor: '#131c31',
                border: '1px solid #1f304f',
                borderRadius: '10px',
                padding: '12px 14px',
                color: '#fff',
                fontSize: '13px',
                boxSizing: 'border-box',
                outline: 'none'
              }}
              required 
            />
          </div>

          {/* Password Input with Eye Button */}
          <div style={{ marginBottom: '24px', position: 'relative' }}>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: '600', color: '#94a3b8', marginBottom: '6px' }}>
              Password
            </label>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <input 
                type={showPassword ? 'text' : 'password'} 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{
                  width: '100%',
                  backgroundColor: '#131c31',
                  border: '1px solid #1f304f',
                  borderRadius: '10px',
                  padding: '12px 42px 12px 14px',
                  color: '#fff',
                  fontSize: '13px',
                  boxSizing: 'border-box',
                  outline: 'none'
                }}
                required 
              />
              <button 
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '12px',
                  background: 'none',
                  border: 'none',
                  color: '#94a3b8',
                  cursor: 'pointer',
                  fontSize: '16px',
                  padding: 0,
                  display: 'flex',
                  alignItems: 'center'
                }}
              >
                {showPassword ? '👁️‍🗨️' : '👁️'}
              </button>
            </div>
          </div>

          {/* Submit Button */}
          <button 
            type="submit" 
            style={{
              width: '100%',
              backgroundColor: '#2563eb',
              color: '#fff',
              border: 'none',
              padding: '13px',
              borderRadius: '10px',
              fontWeight: '600',
              fontSize: '13px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              marginBottom: '16px',
              boxShadow: '0 10px 15px -3px rgba(37, 99, 235, 0.3)'
            }}
          >
            🔒 Access Control Center →
          </button>

          <div style={{ textAlign: 'center', fontSize: '11px', color: '#64748b', margin: '14px 0', fontWeight: '500', letterSpacing: '1px' }}>
            OR
          </div>

          {/* Google Sign-In Button */}
          <button 
            type="button"
            onClick={onLogin}
            style={{
              width: '100%',
              backgroundColor: '#131c31',
              color: '#fff',
              border: '1px solid #1f304f',
              padding: '12px',
              borderRadius: '10px',
              fontWeight: '600',
              fontSize: '13px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
              transition: 'background 0.2s'
            }}
          >
            🌐 Sign in with Google
          </button>
        </form>
      </div>
    </div>
  );
}