import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import ConsensusMeter from './ConsensusMeter';
import './Stage2.css';

function deAnonymizeText(text, labelToModel) {
  if (!labelToModel) return text;

  let result = text;
  Object.entries(labelToModel).forEach(([label, model]) => {
    const modelShortName = model.split('/')[1] || model;
    result = result.replace(new RegExp(label, 'g'), `**${modelShortName}**`);
  });
  return result;
}

export default function Stage2({ rankings, labelToModel, aggregateRankings, consensus }) {
  const [activeTab, setActiveTab] = useState(0);
  const [isExpanded, setIsExpanded] = useState(true);

  if (!rankings || rankings.length === 0) {
    return null;
  }

  const medals = ['🥇', '🥈', '🥉'];

  return (
    <div className="stage stage2-container">
      {/* Header */}
      <div className="stage2-header" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="stage2-title-row">
          <span className="stage2-icon">⚖️</span>
          <div>
            <div className="stage2-title-badge-row">
              <h3 className="stage2-title">Stage 2: Blind Peer Review & Consensus</h3>
              {consensus && (
                <span className={`stage2-header-consensus-tag tier-${consensus.tier || 'moderate'}`}>
                  {consensus.badge_icon || '⚖️'} {consensus.score}% Agreement
                </span>
              )}
            </div>
            <span className="stage2-subtitle">
              Cross-model critique & aggregate rank leaderboard
            </span>
          </div>
        </div>

        <button className="expand-toggle-btn" title="Toggle section">
          {isExpanded ? '▼ Hide Details' : '▶ Show Details'}
        </button>
      </div>

      {isExpanded && (
        <div className="stage2-body">
          {/* Council Consensus & Confidence Meter */}
          {consensus && (
            <ConsensusMeter consensus={consensus} labelToModel={labelToModel} />
          )}

          {/* Aggregate Rankings Leaderboard */}
          {aggregateRankings && aggregateRankings.length > 0 && (
            <div className="leaderboard-section">
              <h4 className="leaderboard-title">🏆 Council Consensus Leaderboard</h4>
              <p className="leaderboard-desc">
                Ranked by average position across all blind peer evaluations (lower score = higher rank).
              </p>

              <div className="leaderboard-grid">
                {aggregateRankings.map((agg, index) => {
                  const shortName = agg.model.split('/')[1] || agg.model;
                  const medal = medals[index] || `#${index + 1}`;
                  return (
                    <div
                      key={index}
                      className={`leaderboard-card ${index === 0 ? 'top-card' : ''}`}
                    >
                      <div className="card-rank-badge">{medal}</div>
                      <div className="card-model-col">
                        <span className="card-model-name" title={agg.model}>
                          {shortName}
                        </span>
                        <span className="card-stats">
                          Score: <strong>{agg.average_rank.toFixed(2)}</strong> • {agg.rankings_count} votes
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Raw Peer Review Tabs */}
          <div className="evaluations-section">
            <h4 className="evaluations-title">🔍 Individual Peer Evaluations</h4>
            <div className="model-tabs">
              {rankings.map((rank, index) => {
                const shortName = rank.model.split('/')[1] || rank.model;
                return (
                  <button
                    key={index}
                    className={`model-tab-btn ${activeTab === index ? 'active' : ''}`}
                    onClick={() => setActiveTab(index)}
                  >
                    <span>{shortName}</span>
                  </button>
                );
              })}
            </div>

            {rankings.length > 0 && (() => {
              const currentReview = rankings[activeTab] || rankings[0];
              if (!currentReview) return null;
              return (
                <div className="evaluation-card">
                  <div className="reviewer-bar">
                    <span>Evaluator: <strong>{currentReview.model}</strong></span>
                  </div>

                  <div className="evaluation-text markdown-content">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {deAnonymizeText(currentReview.ranking || 'Evaluating...', labelToModel)}
                    </ReactMarkdown>
                  </div>

                  {currentReview.parsed_ranking &&
                    currentReview.parsed_ranking.length > 0 && (
                      <div className="extracted-ranking-box">
                        <span className="box-title">Extracted Vote Ranking:</span>
                        <div className="vote-chips-row">
                          {currentReview.parsed_ranking.map((label, i) => {
                            const targetModel =
                              labelToModel && labelToModel[label]
                                ? labelToModel[label].split('/')[1] || labelToModel[label]
                                : label;
                            return (
                              <div key={i} className="vote-chip">
                                <span className="chip-pos">#{i + 1}</span>
                                <span className="chip-name">{targetModel}</span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                </div>
              );
            })()}
          </div>
        </div>
      )}
    </div>
  );
}
