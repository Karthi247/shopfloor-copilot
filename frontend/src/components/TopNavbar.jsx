import React from 'react';
import Icon from './Icon';
import './TopNavbar.css';

export default function TopNavbar({
  pageTitle,
  health,
  user,
  onProfileClick,
  onMenuClick,
  onHelpClick,
}) {
  const isConnected = health?.status === 'ok';
  const initials = (user?.name || 'User')
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase();
  return (
    <header className="top-navbar">
      <div className="top-navbar-title">
        <button
          className="mobile-menu-button"
          aria-label="Open navigation"
          onClick={onMenuClick}
        >
          <Icon name="menu" />
        </button>
        <span className="breadcrumb-root">Operations</span>
        <span className="breadcrumb-divider">/</span>
        <h1>{pageTitle}</h1>
      </div>
      <div className="top-navbar-right">
        <span
          className={`connection-status ${isConnected ? 'connected' : health ? 'disconnected' : 'checking'}`}
        >
          <i />
          {isConnected
            ? 'System connected'
            : health
              ? 'System offline'
              : 'Checking system'}
        </span>
        {health?.indexed_chunks != null && (
          <span className="indexed-count">{health.indexed_chunks} indexed</span>
        )}
        <button className="top-help-button" aria-label="Help" onClick={onHelpClick}>
          ?
        </button>
        <button
          className="top-profile"
          aria-label="Open your profile"
          title={user?.name || 'Profile'}
          onClick={onProfileClick}
        >
          {initials}
        </button>
      </div>
    </header>
  );
}
