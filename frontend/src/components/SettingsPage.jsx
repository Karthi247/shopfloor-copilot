import React, { useState } from 'react';
import Icon from './Icon';
import './SettingsPage.css';

export default function SettingsPage({ health, chatCount, onClearHistory }) {
  const [confirmClear, setConfirmClear] = useState(false);
  return (
    <section className="page-container settings-page">
      <div className="page-heading">
        <div>
          <span className="page-eyebrow">PREFERENCES</span>
          <h2>Settings</h2>
          <p>Workspace status and conversation data for this browser.</p>
        </div>
      </div>
      <section className="settings-panel">
        <div className="settings-panel-heading">
          <span className="settings-panel-icon">
            <Icon name="shield" />
          </span>
          <span>
            <strong>System status</strong>
            <small>Connection and indexed knowledge base</small>
          </span>
        </div>
        <div className="settings-row">
          <span>API connection</span>
          <strong
            className={health?.status === 'ok' ? 'setting-good' : 'setting-offline'}
          >
            <i />
            {health?.status === 'ok' ? 'Connected' : 'Unavailable'}
          </strong>
        </div>
        <div className="settings-row">
          <span>Answer provider</span>
          <strong>
            {health?.provider ? health.provider.toUpperCase() : 'Not available'}
          </strong>
        </div>
        <div className="settings-row">
          <span>Indexed sections</span>
          <strong>{health?.indexed_chunks ?? '—'}</strong>
        </div>
      </section>
      <section className="settings-panel">
        <div className="settings-panel-heading">
          <span className="settings-panel-icon">
            <Icon name="history" />
          </span>
          <span>
            <strong>Conversation history</strong>
            <small>Saved in this browser and not synced to other devices.</small>
          </span>
        </div>
        <div className="history-setting">
          <div>
            <strong>
              {chatCount} saved {chatCount === 1 ? 'conversation' : 'conversations'}
            </strong>
            <p>Conversation history is stored locally in your browser.</p>
          </div>
          <button
            className="clear-history-button"
            disabled={chatCount === 0}
            onClick={() => setConfirmClear(true)}
          >
            <Icon name="trash" size={15} /> Clear history
          </button>
        </div>
      </section>
      {confirmClear && (
        <div
          className="confirm-overlay"
          role="presentation"
          onClick={(event) => {
            if (event.target === event.currentTarget) setConfirmClear(false);
          }}
        >
          <section
            className="confirm-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="clear-history-title"
          >
            <h3 id="clear-history-title">Clear all conversations?</h3>
            <p>This removes saved chats from this browser.</p>
            <div>
              <button className="confirm-cancel" onClick={() => setConfirmClear(false)}>
                Cancel
              </button>
              <button
                className="confirm-delete"
                onClick={() => {
                  onClearHistory();
                  setConfirmClear(false);
                }}
              >
                Clear all chats
              </button>
            </div>
          </section>
        </div>
      )}
    </section>
  );
}
