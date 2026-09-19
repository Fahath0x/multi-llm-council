import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Stage1 from './Stage1';
import Stage2 from './Stage2';
import Stage3 from './Stage3';
import './ChatInterface.css';

// ─── Export Helper ────────────────────────────────────────────────────────────
function buildExportMarkdown(conversation, activePersona) {
  if (!conversation) return '';
  const lines = [];
  lines.push(`# LLM Council — ${conversation.title || 'Deliberation'}`);
  lines.push(`**Mode:** ${activePersona?.icon || ''} ${activePersona?.name || 'Strict Truth & Logic'}`);
  lines.push(`**Exported:** ${new Date().toLocaleString()}`);
  lines.push('');
  lines.push('---');
  lines.push('');
  conversation.messages.forEach((msg) => {
    if (msg.role === 'user') {
      lines.push(`## 🙋 You`);
      lines.push(msg.content);
      lines.push('');
    } else {
      lines.push(`## 🏛️ LLM Council Response`);
      // Stage 1
      if (msg.stage1 && msg.stage1.length > 0) {
        lines.push('### Stage 1 — Individual Opinions');
        msg.stage1.forEach((r) => {
          const name = r.model.split('/')[1] || r.model;
          lines.push(`**${name}:**`);
          lines.push(r.response || '_No response_');
          lines.push('');
        });
      }
      // Stage 3 final answer
      if (msg.stage3?.response) {
        lines.push('### Stage 3 — Chairman Verdict');
        const chairName = msg.stage3.model?.split('/')[1] || msg.stage3.model || 'Chairman';
        lines.push(`*Chairman: ${chairName}*`);
        lines.push('');
        lines.push(msg.stage3.response);
        lines.push('');
      }
      lines.push('---');
      lines.push('');
    }
  });
  return lines.join('\n');
}

function downloadMarkdown(text, filename) {
  const blob = new Blob([text], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ChatInterface({
  conversation,
  onSendMessage,
  isLoading,
  currentSettings,
  availablePersonas,
  onSelectPersona,
  onOpenSettings,
}) {
  const [input, setInput] = useState('');
  const [exportCopied, setExportCopied] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const activePersonaId = currentSettings?.persona || 'strict_truth';
  const activePersona = (availablePersonas || []).find((p) => p.id === activePersonaId) || {
    id: 'strict_truth',
    name: 'Strict Truth & Logic',
    icon: '⚖️',
    badge: 'Strict Truth Engine',
    description: 'Uncompromising accuracy, zero sycophancy, instant error debunking, and mathematical logic.'
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation]);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleRetry = () => {
    if (isLoading || !conversation) return;
    // Find the last user message
    const userMessages = conversation.messages.filter((m) => m.role === 'user');
    if (userMessages.length === 0) return;
    const lastUserMsg = userMessages[userMessages.length - 1];
    onSendMessage(lastUserMsg.content);
  };

  const handleExportChat = () => {
    const md = buildExportMarkdown(conversation, activePersona);
    const safeTitle = (conversation?.title || 'llm-council')
      .toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 40);
    downloadMarkdown(md, `${safeTitle}.md`);
  };

  const handleExportCopy = async () => {
    const md = buildExportMarkdown(conversation, activePersona);
    await navigator.clipboard.writeText(md);
    setExportCopied(true);
    setTimeout(() => setExportCopied(false), 2000);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInputChange = (e) => {
    setInput(e.target.value);
    // Auto resize
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  };

  // Persona-specific Quick Starters
  const starterPrompts = {
    strict_truth: [
      'HTML is a programming language used for machine learning and OS, right?',
      'Is Python always slower than C++? Compare execution and memory.',
      'Explain how Dijkstra algorithm works with a Python implementation.',
      'What are the fatal architectural mistakes in building microservices?',
    ],
    cybersecurity: [
      'Audit this JWT auth & refresh token flow for replay attacks and CSRF vulnerabilities.',
      'How do memory corruption and buffer overflow exploits work in unsafe C code?',
      'Identify critical SSRF and SQL injection attack vectors in a cloud microservice.',
      'Perform a threat model analysis on an OAuth 2.0 PKCE implementation.',
    ],
    code_architect: [
      'Design a multi-region event-driven CDC pipeline handling 250k RPS with zero message loss.',
      'What are the concrete trade-offs between Eventual Consistency vs Strong Consistency in Raft?',
      'Architect a distributed rate limiter in Redis with sliding window and token bucket algorithms.',
      'How to structure a modular Monolith to prevent circular dependencies before scaling?',
    ],
    scientific_proof: [
      'Provide a formal proof of the Halting Problem using Cantor diagonalization.',
      'Derive the backpropagation gradient equations for Multi-Head Self-Attention from first principles.',
      'Prove why Dijkstra algorithm fails with negative edge weights with a counterexample.',
      'Explain the mathematical formulation of Shannon Entropy and KL Divergence in information theory.',
    ],
    product_strategy: [
      'What is the defensible GTM moat for an open-source Developer Tools SaaS targeting enterprise procurement?',
      'How to design a viral developer adoption loop with a bottom-up PLG pricing model?',
      'Evaluate unit economics: $40 CAC, $18 MRR, 4% monthly churn—is this business model sustainable?',
      'What are the unexamined execution risks when pivoting from B2C to enterprise B2B sales?',
    ],
    devils_advocate: [
      'Stress-test the thesis that AI agent swarms will replace all traditional SaaS APIs by 2027.',
      'Challenge the premise that microservices are superior to a clean modular monolith for early-stage startups.',
      'What are the fatal blind spots in replacing relational databases with NoSQL document stores?',
      'Uncover the hidden failure modes in relying entirely on serverless architecture for latency-sensitive workloads.',
    ],
  };

  const quickStarters = starterPrompts[activePersonaId] || starterPrompts.strict_truth;
  const councilModels = currentSettings?.council_models || [];
  const chairmanModel = currentSettings?.chairman_model || '';

  if (!conversation) {
    return (
      <div className="chat-interface">
        <div className="empty-state">
          <div className="empty-logo-glow">🏛️</div>
          <h2>Welcome to LLM Council</h2>
          <p>Create a new deliberation to consult multiple models with blind peer review.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-interface">
      {/* Top Council & Persona Bar */}
      <div className="chat-top-bar">
        <div className="council-chips-wrapper">
          <span className="council-label">Council:</span>
          {councilModels.map((m) => {
            const isChairman = m === chairmanModel;
            const shortName = m.split('/')[1] || m;
            return (
              <span
                key={m}
                className={`council-model-chip ${isChairman ? 'chip-chairman' : ''}`}
                title={m}
              >
                {isChairman ? `👑 ${shortName}` : shortName}
              </span>
            );
          })}
        </div>

        <div className="topbar-right-actions">
          {conversation && conversation.messages.length > 0 && (
            <>
              <button
                className="topbar-export-btn"
                onClick={handleExportChat}
                title="Download conversation as Markdown file"
              >
                <span>📥 Export .md</span>
              </button>
              <button
                className={`topbar-export-btn copy ${exportCopied ? 'copied' : ''}`}
                onClick={handleExportCopy}
                title="Copy full conversation as Markdown to clipboard"
              >
                <span>{exportCopied ? '✓ Copied!' : '📋 Copy MD'}</span>
              </button>
            </>
          )}
          <button className="topbar-settings-btn" onClick={onOpenSettings} title="Configure Council & Personas">
            <span>⚙️ Council Settings</span>
          </button>
        </div>
      </div>

      {/* Persona Mode Switcher Bar */}
      {availablePersonas && availablePersonas.length > 0 && (
        <div className="persona-bar">
          <div className="persona-bar-header">
            <span className="persona-bar-label">🎭 Active Deliberation Mode:</span>
            <span className="persona-desc-hint">{activePersona.description}</span>
          </div>
          <div className="persona-chips-row">
            {availablePersonas.map((p) => {
              const isActive = p.id === activePersonaId;
              return (
                <button
                  key={p.id}
                  className={`persona-chip ${isActive ? 'active' : ''}`}
                  onClick={() => onSelectPersona && onSelectPersona(p.id)}
                  title={p.description}
                >
                  <span className="persona-chip-icon">{p.icon}</span>
                  <span className="persona-chip-name">{p.name}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div className="messages-container">
        {conversation.messages.length === 0 ? (
          <div className="empty-state">
            <div className="empty-logo-glow">{activePersona.icon}</div>
            <h2>{activePersona.name} Deliberation</h2>
            <p className="persona-intro-desc">{activePersona.description}</p>

            {/* Quick Starters */}
            <div className="starters-container">
              <span className="starters-label">Try a specialized inquiry for {activePersona.name}:</span>
              <div className="starters-grid">
                {quickStarters.map((starter, idx) => (
                  <button
                    key={idx}
                    className="starter-card"
                    onClick={() => {
                      setInput(starter);
                      textareaRef.current?.focus();
                    }}
                  >
                    <span className="starter-icon">{activePersona.icon}</span>
                    <span className="starter-text">{starter}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          conversation.messages.map((msg, index) => (
            <div key={index} className="message-group">
              {msg.role === 'user' ? (
                <div className="user-message-card">
                  <div className="user-header">
                    <div className="user-avatar">👤</div>
                    <span className="user-name">You</span>
                  </div>
                  <div className="user-content markdown-content">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                  </div>
                </div>
              ) : (
                <div className="assistant-message-container">
                  <div className="assistant-header">
                    <div className="council-avatar">{msg.metadata?.persona?.icon || activePersona.icon}</div>
                    <div className="council-name-col">
                      <div className="council-name-row">
                        <span className="council-name">LLM Council</span>
                        {msg.metadata?.consensus && (
                          <span className={`council-header-consensus tier-${msg.metadata.consensus.tier || 'moderate'}`}>
                            {msg.metadata.consensus.badge_icon} {msg.metadata.consensus.score}% Consensus
                          </span>
                        )}
                      </div>
                      <span className="deliberation-tag">
                        {msg.metadata?.persona?.badge || activePersona.badge || 'Strict Deliberation Engine'}
                      </span>
                    </div>
                  </div>

                  {/* Stage 1 Loading & Content */}
                  {msg.loading?.stage1 && (
                    <div className="stage-loading stage-loading-1">
                      <div className="loading-spinner"></div>
                      <div className="loading-text-col">
                        <span className="loading-title">Stage 1: Parallel Scrutiny in Progress</span>
                        <span className="loading-desc">Collecting independent first opinions from all council models...</span>
                      </div>
                    </div>
                  )}
                  {msg.stage1 && <Stage1 responses={msg.stage1} />}

                  {/* Stage 2 Loading & Content */}
                  {msg.loading?.stage2 && (
                    <div className="stage-loading stage-loading-2">
                      <div className="loading-spinner"></div>
                      <div className="loading-text-col">
                        <span className="loading-title">Stage 2: Blind Peer Review & Voting</span>
                        <span className="loading-desc">Anonymizing outputs and evaluating cross-model accuracy...</span>
                      </div>
                    </div>
                  )}
                  {msg.stage2 && (
                    <Stage2
                      rankings={msg.stage2}
                      labelToModel={msg.metadata?.label_to_model}
                      aggregateRankings={msg.metadata?.aggregate_rankings}
                      consensus={msg.metadata?.consensus}
                    />
                  )}

                  {/* Stage 3 Loading & Content */}
                  {msg.loading?.stage3 && (
                    <div className="stage-loading stage-loading-3">
                      <div className="loading-spinner spinner-emerald"></div>
                      <div className="loading-text-col">
                        <span className="loading-title text-emerald">Stage 3: Chairman Adjudication</span>
                        <span className="loading-desc">Synthesizing consensus into the solid final answer...</span>
                      </div>
                    </div>
                  )}
                  {msg.stage3 && (
                    <Stage3
                      finalResponse={msg.stage3}
                      consensus={msg.metadata?.consensus}
                    />
                  )}

                  {/* Retry button — shown on last completed assistant message */}
                  {index === conversation.messages.length - 1 &&
                    msg.role === 'assistant' &&
                    !msg.loading?.stage1 &&
                    !msg.loading?.stage2 &&
                    !msg.loading?.stage3 &&
                    msg.stage3 && (
                      <button
                        className="retry-btn"
                        onClick={handleRetry}
                        disabled={isLoading}
                        title="Re-run council with current settings"
                      >
                        🔄 Retry with Current Council
                      </button>
                    )}
                </div>
              )}
            </div>
          ))
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Floating Bottom Input Dock */}
      <div className="input-dock-wrapper">
        <form className="input-dock" onSubmit={handleSubmit}>
          <textarea
            ref={textareaRef}
            className="message-textarea"
            placeholder="Ask anything or propose a technical statement for the Council to judge..."
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            rows={1}
          />
          <button
            type="submit"
            className={`send-btn ${input.trim() && !isLoading ? 'active' : ''}`}
            disabled={!input.trim() || isLoading}
          >
            {isLoading ? (
              <div className="btn-spinner"></div>
            ) : (
              <>
                <span className="send-arrow">➤</span>
                <span className="send-hint">Enter</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
