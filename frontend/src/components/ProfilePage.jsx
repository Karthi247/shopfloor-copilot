import React, { useState } from 'react';
import { updateCurrentUser, updatePassword } from '../services/api';
import Icon from './Icon';
import './ProfilePage.css';

export default function ProfilePage({ user, onUserUpdated, onSignOut }) {
  const [name, setName] = useState(user.name);
  const [email, setEmail] = useState(user.email);
  const [profileBusy, setProfileBusy] = useState(false);
  const [profileMessage, setProfileMessage] = useState(null);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordBusy, setPasswordBusy] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState(null);
  const createdDate = user.created_at
    ? new Date(user.created_at).toLocaleDateString()
    : '—';

  async function saveProfile(event) {
    event.preventDefault();
    setProfileMessage(null);
    setProfileBusy(true);
    try {
      const updated = await updateCurrentUser({ name, email });
      onUserUpdated(updated);
      setName(updated.name);
      setEmail(updated.email);
      setProfileMessage({ type: 'success', text: 'Profile details updated.' });
    } catch (error) {
      setProfileMessage({ type: 'error', text: error.message });
    } finally {
      setProfileBusy(false);
    }
  }

  async function savePassword(event) {
    event.preventDefault();
    setPasswordMessage(null);
    if (newPassword !== confirmPassword) {
      setPasswordMessage({ type: 'error', text: 'The new passwords do not match.' });
      return;
    }
    setPasswordBusy(true);
    try {
      await updatePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setPasswordMessage({ type: 'success', text: 'Password changed successfully.' });
    } catch (error) {
      setPasswordMessage({ type: 'error', text: error.message });
    } finally {
      setPasswordBusy(false);
    }
  }

  return (
    <section className="page-container profile-page">
      <div className="page-heading">
        <div>
          <span className="page-eyebrow">ACCOUNT</span>
          <h2>My profile</h2>
          <p>Manage your account details and sign-in credentials.</p>
        </div>
      </div>
      <div className="profile-summary">
        <span className="profile-large-avatar">
          {(user.name || 'U').trim().slice(0, 1).toUpperCase()}
        </span>
        <span>
          <strong>{user.name}</strong>
          <small>{user.email}</small>
        </span>
        <span className="member-since">Member since {createdDate}</span>
      </div>
      <section className="profile-panel">
        <div className="profile-panel-heading">
          <span className="profile-panel-icon">
            <Icon name="assistant" />
          </span>
          <span>
            <strong>Personal information</strong>
            <small>Update the name and email linked to your account.</small>
          </span>
        </div>
        <form className="profile-form" onSubmit={saveProfile}>
          <div className="profile-fields">
            <label>
              Full name
              <input
                autoComplete="name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                minLength={2}
                maxLength={80}
                required
              />
            </label>
            <label>
              Email address
              <input
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                maxLength={254}
                required
              />
            </label>
          </div>
          {profileMessage && (
            <p
              className={`profile-message ${profileMessage.type}`}
              role={profileMessage.type === 'error' ? 'alert' : 'status'}
            >
              {profileMessage.text}
            </p>
          )}
          <button className="primary-button" type="submit" disabled={profileBusy}>
            {profileBusy ? (
              <>
                <span className="spinner" />
                Saving…
              </>
            ) : (
              'Save profile'
            )}
          </button>
        </form>
      </section>
      <section className="profile-panel">
        <div className="profile-panel-heading">
          <span className="profile-panel-icon">
            <Icon name="shield" />
          </span>
          <span>
            <strong>Change password</strong>
            <small>Use at least 10 characters for your new password.</small>
          </span>
        </div>
        <form className="profile-form" onSubmit={savePassword}>
          <div className="profile-fields">
            <label>
              Current password
              <input
                type="password"
                autoComplete="current-password"
                value={currentPassword}
                onChange={(event) => setCurrentPassword(event.target.value)}
                maxLength={128}
                required
              />
            </label>
            <label>
              New password
              <input
                type="password"
                autoComplete="new-password"
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
                minLength={10}
                maxLength={128}
                required
              />
            </label>
            <label>
              Confirm new password
              <input
                type="password"
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                minLength={10}
                maxLength={128}
                required
              />
            </label>
          </div>
          {passwordMessage && (
            <p
              className={`profile-message ${passwordMessage.type}`}
              role={passwordMessage.type === 'error' ? 'alert' : 'status'}
            >
              {passwordMessage.text}
            </p>
          )}
          <button className="secondary-button" type="submit" disabled={passwordBusy}>
            {passwordBusy ? (
              <>
                <span className="spinner" />
                Updating…
              </>
            ) : (
              'Update password'
            )}
          </button>
        </form>
      </section>
      <section className="profile-signout">
        <div>
          <strong>Sign out</strong>
          <p>End this session on the current browser.</p>
        </div>
        <button className="signout-button" onClick={onSignOut}>
          <Icon name="close" size={15} />
          Sign out
        </button>
      </section>
    </section>
  );
}
