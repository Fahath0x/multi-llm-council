import { useState } from 'react';
import './Sidebar.css';

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  currentSettings,
  availablePersonas,
  onOpenSettings,
}) {
  const [confirmingId, setConfirmingId] = useState(null);

  const councilCount = currentSettings?.council_models?.length || 0;
  const chairmanName = currentSettings?.chairman_model
    ? currentSettings.chairman_model.split('/')[1] || currentSettings.chairman_model
    : 'None';

  const activePersonaId = currentSettings?.persona || 'strict_truth';
  const activePersona = (availablePersonas || []).find((p) => p.id === activePersonaId) || {
    name: 'Strict Truth & Logic',
    icon: '⚖️',
    badge: 'Strict Truth Engine',
  };

  const handleDeleteClick = (e, id) => {
    e.stopPropagation();
    if (confirmingId === id) {
      // Second click — actually delete
      onDeleteConversation && onDeleteConversation(id);
      setConfirmingId(null);
    } else {
      // First click — show confirmation
      setConfirmingId(id);
      setTimeout(() => setConfirmingId((cur) => (cur === id ? null : cur)), 3000);
    }
  };

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div className="sidebar-header">
        <div className="brand-header">
          <div className="brand-logo-glow">{activePersona.icon || '🏛️'}</div>
          <div className="brand-text-col">
            <h1 className="brand-title">LLM Council</h1>
            <div className="status-pill">
              <span className="pulse-dot"></span>
              <span>{activePersona.name}</span>
            </div>
          </div>
        </div>

        <button className="new-conversation-btn" onClick={onNewConversation}>
          <span className="btn-icon">+</span>
          <span>New Deliberation</span>
        </button>
      </div>

      {/* Conversation List */}
      <div className="conversation-list">
        <div className="history-label">DELIBERATION HISTORY</div>
        {conversations.length === 0 ? (
          <div className="no-conversations">
            <div className="empty-icon">💬</div>
            <p>No deliberations yet</p>
            <span>Ask a question to start</span>
          </div>
        ) : (
          conversations.map((conv) => {
            const isActive = conv.id === currentConversationId;
            const isConfirming = confirmingId === conv.id;
            return (
              <div
                key={conv.id}
                className={`conversation-item ${isActive ? 'active' : ''}`}
                onClick={() => onSelectConversation(conv.id)}
              >
                <div className="conv-icon">{isActive ? '🔥' : '💬'}</div>
                <div className="conv-details">
                  <div className="conversation-title" title={conv.title}>
                    {conv.title || 'New Deliberation'}
                  </div>
                  <div className="conversation-meta">
                    {conv.message_count} {conv.message_count === 1 ? 'verdict' : 'verdicts'}
                  </div>
                </div>
                {isActive && <div className="active-glow-indicator"></div>}
                <button
                  className={`conv-delete-btn ${isConfirming ? 'confirming' : ''}`}
                  onClick={(e) => handleDeleteClick(e, conv.id)}
                  title={isConfirming ? 'Click again to confirm delete' : 'Delete deliberation'}
                >
                  {isConfirming ? '✓?' : '🗑️'}
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Sidebar Footer: Active Council & Settings */}
      <div className="sidebar-footer">
        <div className="council-summary-card">
          <div className="summary-header">
            <span className="summary-title">ACTIVE COUNCIL</span>
            <span className="count-badge">{councilCount} Models</span>
          </div>
          <div className="summary-chairman-row">
            <span className="crown-icon">👑</span>
            <div className="chairman-info">
              <span className="chairman-role">Chairman</span>
              <span className="chairman-name" title={currentSettings?.chairman_model}>
                {chairmanName}
              </span>
            </div>
          </div>
          <div className="summary-persona-tag">
            <span>Mode:</span>
            <strong>{activePersona.icon} {activePersona.name}</strong>
          </div>
        </div>

        <button className="settings-btn" onClick={onOpenSettings}>
          <span className="gear-icon">⚙️</span>
          <span>Configure Council</span>
        </button>
      </div>
    </aside>
  );
}
