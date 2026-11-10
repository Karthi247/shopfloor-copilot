import React, { useState } from 'react';
import { signIn, signUp } from '../services/api';
import Icon from './Icon';
import './AuthPage.css';

export default function AuthPage({ onAuthenticated, connectionError = '' }) {
  const [mode, setMode] = useState('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState(connectionError);
  const [busy, setBusy] = useState(false);
  const isSignup = mode === 'signup';

  async function submit(event) {
    event.preventDefault();
    setError('');
    if (isSignup && password !== confirmPassword) {
      setError('The passwords do not match.');
      return;
    }
    setBusy(true);
    try {
      const result = isSignup
        ? await signUp({ name, email, password })
        : await signIn({ email, password });
      onAuthenticated(result.user);
    } catch (reason) {
      setError(reason.message || 'We couldn’t complete that request. Try again.');
    } finally {
      setBusy(false);
    }
  }

  function switchMode(nextMode) {
    setMode(nextMode);
    setError('');
    setPassword('');
    setConfirmPassword('');
  }

  return (
    <main className="auth-shell">
      <div className="auth-top-brand">
        <span className="auth-mark">SF</span>
        <span>
          <strong>SHOPFLOOR</strong>
          <small>AI COPILOT</small>
        </span>
      </div>
      <div className="auth-layout">
        <section className="auth-intro">
          <span className="auth-intro-icon">
            <Icon name="spark" size={20} />
          </span>
          <span className="auth-kicker">SHOPFLOOR KNOWLEDGE</span>
          <h1>Reliable answers for the work in front of you.</h1>
          <p>
            Access your manufacturing SOPs, maintenance manuals, and safety procedures
            in one private workspace.
          </p>
          <div className="auth-benefits">
            <span>
              <Icon name="document" size={16} /> Answers grounded in indexed procedures
            </span>
            <span>
              <Icon name="shield" size={16} /> Source references and revision context
            </span>
          </div>
        </section>
        <section className="auth-card" aria-labelledby="auth-title">
          <div className="auth-card-heading">
            <span className="auth-kicker">PRIVATE WORKSPACE</span>
            <h2 id="auth-title">{isSignup ? 'Create your account' : 'Welcome back'}</h2>
            <p>
              {isSignup
                ? 'Set up an account to save your chat history and profile.'
                : 'Sign in to continue to your ShopFloor assistant.'}
            </p>
          </div>
          <div className="auth-tabs" role="tablist" aria-label="Account access">
            <button
              role="tab"
              aria-selected={!isSignup}
              className={!isSignup ? 'selected' : ''}
              onClick={() => switchMode('login')}
            >
              Sign in
            </button>
            <button
              role="tab"
              aria-selected={isSignup}
              className={isSignup ? 'selected' : ''}
              onClick={() => switchMode('signup')}
            >
              Create account
            </button>
          </div>
          <form className="auth-form" onSubmit={submit}>
            {isSignup && (
              <label>
                Full name
                <input
                  autoComplete="name"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Your name"
                  minLength={2}
                  maxLength={80}
                  required
                />
              </label>
            )}
            <label>
              Email address
              <input
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@company.com"
                maxLength={254}
                required
              />
            </label>
            <label>
              Password
              <input
                type="password"
                autoComplete={isSignup ? 'new-password' : 'current-password'}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder={
                  isSignup ? 'At least 10 characters' : 'Enter your password'
                }
                minLength={isSignup ? 10 : 1}
                maxLength={128}
                required
              />
            </label>
            {isSignup && (
              <label>
                Confirm password
                <input
                  type="password"
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  placeholder="Enter the password again"
                  minLength={10}
                  maxLength={128}
                  required
                />
              </label>
            )}
            {error && (
              <div className="auth-error" role="alert">
                {error}
              </div>
            )}
            <button className="auth-submit" type="submit" disabled={busy}>
              {busy ? (
                <>
                  <span className="spinner" />
                  {isSignup ? 'Creating account…' : 'Signing in…'}
                </>
              ) : isSignup ? (
                'Create account'
              ) : (
                'Sign in'
              )}
              <Icon name="send" size={15} />
            </button>
          </form>
          <p className="auth-footnote">
            Your account is stored in this application’s local database. Chat history
            stays in this browser.
          </p>
        </section>
      </div>
      <footer className="auth-footer">
        SHOPFLOOR AI COPILOT <span>·</span> KAVERI PRECISION COMPONENTS
      </footer>
    </main>
  );
}
