import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './Stage3.css';

export default function Stage3({ finalResponse, consensus }) {
  const [copied, setCopied] = useState(false);

  if (!finalResponse) {
    return null;
  }

  const chairmanName = finalResponse.model.split('/')[1] || finalResponse.model;

  const handleCopy = () => {
    if (finalResponse.response) {
      navigator.clipboard.writeText(finalResponse.response);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const isStreaming = finalResponse.streaming;

  return (
    <div className={`stage stage3-container ${isStreaming ? 'stage3-streaming-active' : ''}`}>
      {/* Header Banner */}
      <div className="stage3-header">
        <div className="stage3-title-row">
          <span className="verdict-icon">⚖️</span>
          <div>
            <div className="stage3-title-with-badge">
              <h3 className="stage3-title">Stage 3: Definitive Council Verdict</h3>
              {isStreaming && (
                <span className="streaming-badge">
                  <span className="streaming-pulse-dot"></span>
                  ⚡ Streaming Real-Time
                </span>
              )}
            </div>
            <span className="stage3-subtitle">
              {isStreaming
                ? 'Chairman model generating live token-by-token synthesis...'
                : 'Synthesized & Adjudicated Final Answer'}
            </span>
          </div>
        </div>

        <div className="stage3-actions">
          {consensus && (
            <div
              className={`stage3-confidence-pill tier-${consensus.tier || 'moderate'}`}
              title={`Council Agreement: ${consensus.score}% (${consensus.tier_label})`}
            >
              <span className="conf-icon">{consensus.badge_icon || '🎯'}</span>
              <span className="conf-label">Confidence:</span>
              <strong className="conf-score">{consensus.score}%</strong>
            </div>
          )}

          <div className="chairman-tag">
            <span className="crown-emoji">👑</span>
            <span>Chairman: <strong>{chairmanName}</strong></span>
          </div>

          {!isStreaming && (
            <button className="copy-btn" onClick={handleCopy} title="Copy final answer">
              {copied ? '✓ Copied!' : '📋 Copy Answer'}
            </button>
          )}
        </div>
      </div>

      {/* Answer Body */}
      <div className="stage3-body">
        <div className="final-text markdown-content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {finalResponse.response || (isStreaming ? '...' : '')}
          </ReactMarkdown>
          {isStreaming && <span className="streaming-cursor">▋</span>}
        </div>
      </div>
    </div>
  );
}
