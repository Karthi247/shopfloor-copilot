import React, { useState } from 'react';
import AnswerMarkdown from './AnswerMarkdown';
import SourceCard from './SourceCard';
import Icon from './Icon';

export default function ChatMessage({ message, busy, onEdit, onRetry }) {
  if (message.role === 'user')
    return (
      <article className="chat-message user-message">
        <div className="message-avatar user-avatar">KP</div>
        <div className="message-content">
          <div className="message-author">You</div>
          <p className="user-message-text">{message.content}</p>
          <button
            className="message-action-button edit-question-button"
            type="button"
            disabled={busy}
            onClick={onEdit}
          >
            <Icon name="edit" size={14} /> Edit question
          </button>
        </div>
      </article>
    );

  if (message.error)
    return (
      <article className="chat-message assistant-message">
        <div className="message-avatar assistant-avatar">SF</div>
        <div className="message-content">
          <div className="message-author">ShopFloor Copilot</div>
          <div className="chat-error" role="alert">
            <strong>Couldn’t complete the request</strong>
            <span>{message.error}</span>
            <button
              className="message-action-button retry-answer-button"
              type="button"
              disabled={busy}
              onClick={onRetry}
            >
              <Icon name="retry" size={14} /> Retry answer
            </button>
          </div>
        </div>
      </article>
    );

  const result = message.result || {};
  const answer = message.answer || result.answer || '';
  return (
    <article
      className={`chat-message assistant-message ${result.safety_critical ? 'safety-critical-message' : ''}`}
    >
      <div className="message-avatar assistant-avatar">SF</div>
      <div className="message-content">
        <div className="message-author">
          ShopFloor Copilot
          <span
            className={`answer-status ${result.answered ? 'supported' : 'unsupported'}`}
          >
            <i />
            {result.answered ? 'Source-backed' : 'No matching source'}
          </span>
        </div>
        {result.safety_critical && (
          <div className="safety-warning" role="note">
            <Icon name="safety" size={18} />
            <span>
              <strong>Safety-critical guidance</strong>
              <small>
                Check the cited procedure and follow posted safety controls and your
                authorized supervisor’s direction.
              </small>
            </span>
          </div>
        )}
        <AnswerMarkdown>{answer}</AnswerMarkdown>
        {result.revision_note && (
          <p className="revision-note">{result.revision_note}</p>
        )}
        {result.sources?.length > 0 && (
          <section className="message-sources">
            <div className="message-sources-heading">
              Source documents <span>{result.sources.length}</span>
            </div>
            {result.sources.map((source, index) => (
              <SourceCard
                key={`${source.filename}-${source.page}-${index}`}
                source={source}
              />
            ))}
          </section>
        )}
        {result.answered && <CopyAnswer answer={answer} />}
      </div>
    </article>
  );
}

function CopyAnswer({ answer }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    try {
      await navigator.clipboard.writeText(answer);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  }
  return (
    <button className="copy-answer-button" onClick={copy} aria-label="Copy answer">
      <Icon name={copied ? 'check' : 'copy'} size={14} />
      {copied ? 'Copied' : 'Copy answer'}
    </button>
  );
}
