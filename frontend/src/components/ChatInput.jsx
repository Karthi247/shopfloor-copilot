import React, { useLayoutEffect, useRef } from 'react';
import Icon from './Icon';

export default function ChatInput({
  question,
  setQuestion,
  onSubmit,
  busy,
  inputRef,
  compact = false,
  editing = false,
}) {
  const lastPointerSendAt = useRef(0);

  useLayoutEffect(() => {
    const textarea = inputRef?.current;
    if (!textarea) return;
    textarea.style.height = 'auto';
    const maxHeight = Number.parseFloat(window.getComputedStyle(textarea).maxHeight);
    textarea.style.height = `${Math.min(textarea.scrollHeight, maxHeight)}px`;
  }, [inputRef, question]);

  function sendQuestion(event) {
    if (event) {
      const now = Date.now();
      if (now - lastPointerSendAt.current < 500) return;
      lastPointerSendAt.current = now;
    }

    const value = (inputRef?.current?.value || question).trim();
    if (!value || busy) return;
    onSubmit(value);
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendQuestion();
    }
  }
  return (
    <form
      className={`chat-composer ${compact ? 'compact' : ''}`}
      onSubmit={(event) => {
        event.preventDefault();
        sendQuestion();
      }}
    >
      <label className="sr-only" htmlFor="chat-question">
        Ask the ShopFloor assistant
      </label>
      <div className="chat-composer-heading">
        <span className="chat-composer-heading-icon">
          <Icon name="spark" size={15} />
        </span>
        <strong>{editing ? 'Editing your question' : 'Ask ShopFloor Copilot'}</strong>
        <span>
          {editing ? 'Update the question, then retry' : 'Document-grounded answers'}
        </span>
      </div>
      <textarea
        id="chat-question"
        ref={inputRef}
        rows="1"
        maxLength="1000"
        value={question}
        placeholder="Ask a question about your shop-floor procedures…"
        onChange={(event) => setQuestion(event.target.value)}
        onKeyDown={handleKeyDown}
      />
      <div className="chat-composer-footer">
        <span>
          Enter to send <i>·</i> Shift + Enter for a new line
        </span>
        <button
          type="button"
          onPointerUp={sendQuestion}
          onTouchEnd={(event) => {
            event.preventDefault();
            sendQuestion(event);
          }}
          onClick={sendQuestion}
          disabled={!question.trim() || busy}
          aria-label={
            busy ? 'Searching documents' : editing ? 'Update and retry' : 'Send message'
          }
        >
          {busy ? <span className="spinner" /> : <Icon name="send" size={17} />}
        </button>
      </div>
    </form>
  );
}
