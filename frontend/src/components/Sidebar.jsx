import React from 'react';
import Icon from './Icon';
import './Sidebar.css';

function NavItem({ icon, children, active, onClick }) {
  return (
    <button
      className={`sidebar-nav-item ${active ? 'active' : ''}`}
      aria-current={active ? 'page' : undefined}
      onClick={onClick}
    >
      <Icon name={icon} size={17} /> <span>{children}</span>
    </button>
  );
}

export default function Sidebar({
  page,
  setPage,
  user,
  onOpenProfile,
  chats,
  activeChatId,
  openChat,
  startNewChat,
  deleteChat,
  search,
  setSearch,
  isOpen,
  close,
}) {
  const filteredChats = chats.filter((chat) =>
    (chat.title || '').toLowerCase().includes(search.trim().toLowerCase()),
  );
  const initials = (user?.name || 'User')
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase();
  return (
    <>
      {isOpen && (
        <button
          className="sidebar-overlay"
          aria-label="Close navigation"
          onClick={close}
        />
      )}
      <aside
        className={`sidebar ${isOpen ? 'sidebar-open' : ''}`}
        aria-label="Main navigation"
      >
        <div className="sidebar-brand-row">
          <button
            className="sidebar-brand"
            onClick={startNewChat}
            aria-label="ShopFloor AI Copilot home"
          >
            <span className="brand-mark">SF</span>
            <span>
              <strong>SHOPFLOOR</strong>
              <small>AI COPILOT</small>
            </span>
          </button>
          <button
            className="sidebar-close"
            aria-label="Close navigation"
            onClick={close}
          >
            <Icon name="close" />
          </button>
        </div>
        <button className="new-chat-button" onClick={startNewChat}>
          <Icon name="plus" size={17} />
          <span>New chat</span>
        </button>
        <div className="sidebar-section-label">WORKSPACE</div>
        <nav className="sidebar-navigation">
          <NavItem
            icon="assistant"
            active={page === 'assistant'}
            onClick={startNewChat}
          >
            Chat Assistant
          </NavItem>
          <NavItem
            icon="document"
            active={page === 'documents'}
            onClick={() => {
              setPage('documents');
              close();
            }}
          >
            Document Library
          </NavItem>
        </nav>
        <section className="sidebar-history" aria-label="Recent conversations">
          <div className="sidebar-history-heading">
            <span>RECENT CONVERSATIONS</span>
            <span>{chats.length}</span>
          </div>
          <label className="sidebar-search">
            <Icon name="search" size={15} />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search conversations"
              aria-label="Search conversations"
            />
          </label>
          <div className="sidebar-chat-list">
            {filteredChats.map((chat) => (
              <div
                className={`sidebar-chat-row ${chat.id === activeChatId ? 'selected' : ''}`}
                key={chat.id}
              >
                <button
                  className="sidebar-chat-open"
                  title={chat.title}
                  onClick={() => {
                    openChat(chat.id);
                    close();
                  }}
                >
                  <Icon name="history" size={15} />
                  <span>{chat.title}</span>
                </button>
                <button
                  className="sidebar-chat-delete"
                  title="Delete conversation"
                  aria-label={`Delete conversation: ${chat.title}`}
                  onClick={(event) => deleteChat(event, chat.id)}
                >
                  <Icon name="trash" size={14} />
                </button>
              </div>
            ))}
            {!filteredChats.length && (
              <p className="sidebar-empty">
                {chats.length
                  ? 'No conversations match your search.'
                  : 'Your saved conversations will appear here.'}
              </p>
            )}
          </div>
        </section>
        <div className="sidebar-footer">
          <NavItem
            icon="settings"
            active={page === 'settings'}
            onClick={() => {
              setPage('settings');
              close();
            }}
          >
            Settings
          </NavItem>
          <button
            className={`sidebar-profile ${page === 'profile' ? 'active' : ''}`}
            onClick={onOpenProfile}
            aria-label="Open your profile"
          >
            <span className="profile-avatar">{initials}</span>
            <span className="profile-copy">
              <strong>{user?.name}</strong>
              <small>{user?.email}</small>
            </span>
            <span className="profile-status" title="Signed in" />
          </button>
        </div>
      </aside>
    </>
  );
}
