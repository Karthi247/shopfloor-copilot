import React, { useEffect, useRef, useState } from 'react';
import {
  askCopilot,
  getCurrentUser,
  getDocuments,
  getHealth,
  signOut,
} from './services/api';
import AuthPage from './components/AuthPage';
import ChatInput from './components/ChatInput';
import ChatMessage from './components/ChatMessage';
import DocumentLibrary from './components/DocumentLibrary';
import Icon from './components/Icon';
import SettingsPage from './components/SettingsPage';
import Sidebar from './components/Sidebar';
import TopNavbar from './components/TopNavbar';
import WelcomeScreen from './components/WelcomeScreen';
import ProfilePage from './components/ProfilePage';
import './components/ChatInterface.css';

const HISTORY_KEY_PREFIX = 'shopfloor-ai-copilot.history.v1.';
const MAX_CONVERSATIONS = 50;

function loadHistory(userId) {
  try {
    const saved = JSON.parse(
      localStorage.getItem(`${HISTORY_KEY_PREFIX}${userId}`) || '[]',
    );
    if (!Array.isArray(saved)) return [];
    return saved
      .filter((chat) => chat?.id && Array.isArray(chat.messages))
      .map((chat) => ({
        ...chat,
        title: typeof chat.title === 'string' ? chat.title : 'Untitled conversation',
        updatedAt:
          typeof chat.updatedAt === 'string'
            ? chat.updatedAt
            : chat.createdAt || new Date(0).toISOString(),
        messages: chat.messages.filter(
          (message) => message && ['user', 'assistant'].includes(message.role),
        ),
      }))
      .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))
      .slice(0, MAX_CONVERSATIONS);
  } catch {
    return [];
  }
}

export default function App() {
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [authError, setAuthError] = useState('');

  useEffect(() => {
    let mounted = true;
    getCurrentUser()
      .then((currentUser) => {
        if (mounted) setUser(currentUser);
      })
      .catch((error) => {
        if (mounted) setAuthError(error.message);
      })
      .finally(() => {
        if (mounted) setAuthLoading(false);
      });
    const handleExpired = () => {
      setUser(null);
      setAuthError('Your session expired. Please sign in again.');
    };
    window.addEventListener('shopfloor-auth-expired', handleExpired);
    return () => {
      mounted = false;
      window.removeEventListener('shopfloor-auth-expired', handleExpired);
    };
  }, []);

  if (authLoading)
    return (
      <main className="auth-loading">
        <span className="spinner" />
        Checking your session…
      </main>
    );
  if (!user)
    return (
      <AuthPage
        connectionError={authError}
        onAuthenticated={(nextUser) => {
          setAuthError('');
          setUser(nextUser);
        }}
      />
    );
  return (
    <Workspace
      key={user.id}
      user={user}
      onUserUpdated={setUser}
      onSignOut={() => {
        signOut();
        setUser(null);
      }}
    />
  );
}

function Workspace({ user, onUserUpdated, onSignOut }) {
  const [page, setPage] = useState('assistant');
  const [chats, setChats] = useState(() => loadHistory(user.id));
  const [activeChatId, setActiveChatId] = useState(null);
  const [historySearch, setHistorySearch] = useState('');
  const [question, setQuestion] = useState('');
  const [editTarget, setEditTarget] = useState(null);
  const [busyChatId, setBusyChatId] = useState(null);
  const [health, setHealth] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [documentsLoading, setDocumentsLoading] = useState(true);
  const [documentsError, setDocumentsError] = useState('');
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const inputRef = useRef(null);
  const bottomRef = useRef(null);

  const activeChat = chats.find((chat) => chat.id === activeChatId);
  const messages = activeChat?.messages || [];

  useEffect(() => {
    try {
      localStorage.setItem(
        `${HISTORY_KEY_PREFIX}${user.id}`,
        JSON.stringify(chats.slice(0, MAX_CONVERSATIONS)),
      );
    } catch {
      /* Local storage can be disabled or full. */
    }
  }, [chats, user.id]);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth({ status: 'offline' }));
    getDocuments()
      .then(setDocuments)
      .catch((error) => setDocumentsError(error.message))
      .finally(() => setDocumentsLoading(false));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages.length, busyChatId, activeChatId]);

  function newChat() {
    setPage('assistant');
    setActiveChatId(null);
    setQuestion('');
    setEditTarget(null);
    setSidebarOpen(false);
    inputRef.current?.focus();
  }

  function openChat(id) {
    setPage('assistant');
    setActiveChatId(id);
    setQuestion('');
    setEditTarget(null);
    setSidebarOpen(false);
  }

  function deleteChat(event, id) {
    event.stopPropagation();
    setChats((previous) => previous.filter((chat) => chat.id !== id));
    if (activeChatId === id) {
      setActiveChatId(null);
      setQuestion('');
      setEditTarget(null);
    }
  }

  function clearHistory() {
    setChats([]);
    setActiveChatId(null);
    setQuestion('');
    setEditTarget(null);
  }

  function toApiHistory(messagesToConvert) {
    return messagesToConvert
      .map((message) => {
        if (message.role === 'user')
          return { role: 'user', content: message.content };
        return message.result?.answer
          ? { role: 'assistant', content: message.result.answer }
          : null;
      })
      .filter(Boolean)
      .slice(-6);
  }

  async function runQuestion(
    value,
    { chatId = activeChatId, replaceFromIndex = null } = {},
  ) {
    const text = value.trim();
    if (!text || busyChatId) return;
    const existingChat = chats.find((chat) => chat.id === chatId);
    const id = existingChat?.id || crypto.randomUUID();
    const now = new Date().toISOString();
    const title =
      existingChat?.title ||
      (text.length > 48 ? `${text.slice(0, 48).trimEnd()}…` : text);
    const previousMessages = existingChat?.messages || [];
    const historyMessages =
      replaceFromIndex === null
        ? previousMessages
        : previousMessages.slice(0, replaceFromIndex);
    const history = toApiHistory(historyMessages);

    setPage('assistant');
    setActiveChatId(id);
    setQuestion('');
    setEditTarget(null);
    setBusyChatId(id);
    setChats((previous) => {
      const exists = previous.some((chat) => chat.id === id);
      const updated = exists
        ? previous.map((chat) =>
            chat.id === id
              ? {
                  ...chat,
                  updatedAt: now,
                  messages: [
                    ...(replaceFromIndex === null
                      ? chat.messages
                      : chat.messages.slice(0, replaceFromIndex)),
                    { role: 'user', content: text },
                  ],
                }
              : chat,
          )
        : [
            {
              id,
              title,
              createdAt: now,
              updatedAt: now,
              messages: [{ role: 'user', content: text }],
            },
            ...previous,
          ];
      return updated
        .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))
        .slice(0, MAX_CONVERSATIONS);
    });

    try {
      const result = await askCopilot(text, history);
      setChats((previous) =>
        previous.map((chat) =>
          chat.id === id
            ? {
                ...chat,
                updatedAt: new Date().toISOString(),
                messages: [
                  ...chat.messages,
                  { role: 'assistant', answer: result.answer, result },
                ],
              }
            : chat,
        ),
      );
    } catch (error) {
      setChats((previous) =>
        previous.map((chat) =>
          chat.id === id
            ? {
                ...chat,
                updatedAt: new Date().toISOString(),
                messages: [
                  ...chat.messages,
                  { role: 'assistant', error: error.message },
                ],
              }
            : chat,
        ),
      );
    } finally {
      setBusyChatId(null);
    }
  }

  async function submit(value = question) {
    await runQuestion(value, {
      chatId: editTarget?.chatId || activeChatId,
      replaceFromIndex: editTarget?.index ?? null,
    });
  }

  function retryQuestion(chatId, userIndex) {
    const chat = chats.find((item) => item.id === chatId);
    const message = chat?.messages[userIndex];
    if (message?.role !== 'user') return;
    runQuestion(message.content, { chatId, replaceFromIndex: userIndex });
  }

  function editQuestion(chatId, userIndex) {
    const chat = chats.find((item) => item.id === chatId);
    const message = chat?.messages[userIndex];
    if (message?.role !== 'user' || busyChatId) return;
    setPage('assistant');
    setActiveChatId(chatId);
    setEditTarget({ chatId, index: userIndex });
    setQuestion(message.content);
    window.setTimeout(() => inputRef.current?.focus(), 0);
  }

  function cancelEdit() {
    setEditTarget(null);
    setQuestion('');
    inputRef.current?.focus();
  }

  const pageTitles = {
    assistant: activeChat?.title || 'Chat Assistant',
    documents: 'Document Library',
    settings: 'Settings',
    profile: 'My profile',
  };
  return (
    <div className="app-shell">
      <Sidebar
        page={page}
        setPage={(nextPage) => {
          setPage(nextPage);
          setSidebarOpen(false);
        }}
        user={user}
        onOpenProfile={() => {
          setPage('profile');
          setSidebarOpen(false);
        }}
        chats={chats}
        activeChatId={activeChatId}
        openChat={openChat}
        startNewChat={newChat}
        deleteChat={deleteChat}
        search={historySearch}
        setSearch={setHistorySearch}
        isOpen={isSidebarOpen}
        close={() => setSidebarOpen(false)}
      />
      <main className="main-content">
        <TopNavbar
          pageTitle={pageTitles[page]}
          health={health}
          user={user}
          onProfileClick={() => setPage('profile')}
          onMenuClick={() => setSidebarOpen(true)}
          onHelpClick={() => setHelpOpen(true)}
        />
        {page === 'documents' && (
          <DocumentLibrary
            documents={documents}
            loading={documentsLoading}
            error={documentsError}
          />
        )}
        {page === 'settings' && (
          <SettingsPage
            health={health}
            chatCount={chats.length}
            onClearHistory={clearHistory}
          />
        )}
        {page === 'profile' && (
          <ProfilePage
            user={user}
            onUserUpdated={onUserUpdated}
            onSignOut={onSignOut}
          />
        )}
        {page === 'assistant' && (
          <section
            className={`chat-page ${messages.length ? 'has-messages' : 'is-empty'}`}
          >
            {messages.length === 0 ? (
              <WelcomeScreen
                onAsk={submit}
                composer={
                  <ChatInput
                    question={question}
                    setQuestion={setQuestion}
                    onSubmit={submit}
                    busy={Boolean(busyChatId)}
                    inputRef={inputRef}
                  />
                }
              />
            ) : (
              <>
                <div className="conversation-scroll">
                  <div className="conversation-column">
                    {messages.map((message, index) => (
                      <ChatMessage
                        key={`${activeChatId}-${index}`}
                        message={message}
                        busy={Boolean(busyChatId)}
                        onEdit={() => editQuestion(activeChatId, index)}
                        onRetry={() => retryQuestion(activeChatId, index - 1)}
                      />
                    ))}
                    {busyChatId === activeChatId && (
                      <div className="assistant-loading">
                        <span className="spinner light" />
                        <span>Searching indexed procedures…</span>
                      </div>
                    )}
                    <div ref={bottomRef} />
                  </div>
                </div>
                <div className="chat-input-dock conversation-dock">
                  {editTarget && (
                    <div className="chat-editing-banner">
                      <span>Editing your question</span>
                      <button type="button" onClick={cancelEdit}>
                        Cancel
                      </button>
                    </div>
                  )}
                  <ChatInput
                    question={question}
                    setQuestion={setQuestion}
                    onSubmit={submit}
                    busy={Boolean(busyChatId)}
                    inputRef={inputRef}
                    compact
                    editing={Boolean(editTarget)}
                    onCancel={cancelEdit}
                  />
                </div>
              </>
            )}
            <p className="chat-disclaimer">
              <Icon name="shield" size={13} /> Answers are grounded in indexed
              procedures. Always follow posted safety controls and your authorized
              supervisor’s direction.
            </p>
          </section>
        )}
      </main>
      {helpOpen && (
        <div
          className="modal-backdrop"
          role="presentation"
          onClick={(event) => {
            if (event.target === event.currentTarget) setHelpOpen(false);
          }}
        >
          <section
            className="help-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="help-title"
          >
            <button
              className="help-close"
              aria-label="Close help"
              onClick={() => setHelpOpen(false)}
            >
              <Icon name="close" />
            </button>
            <span className="page-eyebrow">SHOPFLOOR AI COPILOT</span>
            <h2 id="help-title">How can I help?</h2>
            <p>
              Ask a question about an indexed maintenance, quality, or safety procedure.
              Answers include source documents and page numbers when supporting evidence
              is available.
            </p>
            <p>
              Use Document Library to review indexed procedures and their current
              revisions. Your conversation history is saved in this browser.
            </p>
            <button className="primary-button" onClick={() => setHelpOpen(false)}>
              Got it
            </button>
          </section>
        </div>
      )}
    </div>
  );
}
