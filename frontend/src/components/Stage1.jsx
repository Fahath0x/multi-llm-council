import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './Stage1.css';

export default function Stage1({ responses }) {
  const [activeTab, setActiveTab] = useState(0);
  const [isExpanded, setIsExpanded] = useState(false);

  if (!responses || responses.length === 0) {
    return null;
  }

  return (
    <div className="stage stage1-container">
      {/* Header */}
      <div className="stage1-header" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="stage1-title-row">
          <span className="stage1-icon">💡</span>
          <div>
            <h3 className="stage1-title">Stage 1: Individual First Opinions</h3>
            <span className="stage1-subtitle">
              Parallel responses from {responses.length} council models
            </span>
          </div>
        </div>

        <button className="stage1-toggle-btn" title="Toggle section">
          {isExpanded ? '▼ Hide First Opinions' : '▶ Inspect All Initial Answers'}
        </button>
      </div>

      {isExpanded && (
        <div className="stage1-body">
          {/* Model Tabs */}
          <div className="stage1-tabs">
            {responses.map((resp, index) => {
              const shortName = resp.model.split('/')[1] || resp.model;
              return (
                <button
                  key={index}
                  className={`stage1-tab-btn ${activeTab === index ? 'active' : ''}`}
                  onClick={() => setActiveTab(index)}
                >
                  {shortName}
                </button>
              );
            })}
          </div>

          {/* Response Content */}
          {responses[activeTab] && (
            <div className="stage1-content-card">
              <div className="stage1-model-bar">
                <span>Model: <strong>{responses[activeTab].model}</strong></span>
              </div>
              <div className="stage1-response-text markdown-content">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {responses[activeTab].response || 'Waiting for model response...'}
                </ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
