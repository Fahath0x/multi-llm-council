import React, { useState } from 'react';
import './ConsensusMeter.css';

export default function ConsensusMeter({ consensus, labelToModel }) {
  const [showMatrix, setShowMatrix] = useState(false);

  if (!consensus) {
    return null;
  }

  const {
    score = 0,
    tier = 'moderate',
    tier_label = 'Moderate Consensus',
    badge_icon = '⚖️',
    kendall_w = 0,
    top_pick_agreement_pct = 0,
    total_voters = 0,
    summary = '',
    vote_matrix = []
  } = consensus;

  // SVG Gauge calculations
  const size = 110;
  const strokeWidth = 9;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  // Tier color mapping
  const getTierClass = (t) => {
    switch (t) {
      case 'unanimous':
        return 'tier-unanimous';
      case 'strong':
        return 'tier-strong';
      case 'moderate':
        return 'tier-moderate';
      case 'contested':
      default:
        return 'tier-contested';
    }
  };

  const getTierColor = (t) => {
    switch (t) {
      case 'unanimous':
        return '#10b981'; // Emerald
      case 'strong':
        return '#22c55e'; // Green
      case 'moderate':
        return '#f59e0b'; // Amber
      case 'contested':
      default:
        return '#f43f5e'; // Rose
    }
  };

  const tierClass = getTierClass(tier);
  const tierColor = getTierColor(tier);

  // Extract candidate models from labelToModel or vote_matrix
  const candidates = labelToModel ? Object.values(labelToModel) : [];

  return (
    <div className={`consensus-meter-card ${tierClass}`}>
      <div className="consensus-main-row">
        {/* Left: Animated Radial Gauge */}
        <div className="gauge-wrapper">
          <svg className="gauge-svg" width={size} height={size}>
            {/* Background Track */}
            <circle
              className="gauge-track"
              cx={size / 2}
              cy={size / 2}
              r={radius}
              strokeWidth={strokeWidth}
            />
            {/* Animated Progress Ring */}
            <circle
              className="gauge-progress"
              cx={size / 2}
              cy={size / 2}
              r={radius}
              strokeWidth={strokeWidth}
              stroke={tierColor}
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              transform={`rotate(-90 ${size / 2} ${size / 2})`}
            />
          </svg>
          <div className="gauge-inner-label">
            <span className="gauge-score-value">{score}%</span>
            <span className="gauge-score-label">AGREEMENT</span>
          </div>
        </div>

        {/* Center/Right: Consensus Stats & Summary */}
        <div className="consensus-info-col">
          <div className="consensus-badge-row">
            <span className={`consensus-tier-badge ${tierClass}`}>
              <span className="tier-icon">{badge_icon}</span>
              <span className="tier-name">{tier_label}</span>
            </span>
            <span className="voters-badge">
              👥 {total_voters} Council Voters
            </span>
          </div>

          <p className="consensus-summary-text">{summary}</p>

          <div className="consensus-metrics-pills">
            <div className="metric-pill" title="Percentage of models that chose the winning model as #1">
              <span className="metric-pill-label">Top Pick Alignment:</span>
              <span className="metric-pill-val">{top_pick_agreement_pct}%</span>
            </div>
            <div className="metric-pill" title="Kendall's Coefficient of Concordance (0 = complete disagreement, 1 = unanimous rank order)">
              <span className="metric-pill-label">Rank Concordance (W):</span>
              <span className="metric-pill-val">{kendall_w.toFixed(2)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Expandable Stance / Voting Alignment Matrix */}
      {vote_matrix && vote_matrix.length > 0 && candidates.length > 0 && (
        <div className="stance-matrix-section">
          <button
            className="toggle-matrix-btn"
            onClick={() => setShowMatrix(!showMatrix)}
            type="button"
          >
            <span>{showMatrix ? '▲ Hide Stance Matrix' : '📊 View Inter-Model Stance Matrix'}</span>
          </button>

          {showMatrix && (
            <div className="matrix-table-container">
              <table className="stance-table">
                <thead>
                  <tr>
                    <th className="table-corner">Evaluator \ Candidate</th>
                    {candidates.map((cand, idx) => {
                      const candShort = cand.split('/')[1] || cand;
                      return (
                        <th key={idx} className="candidate-header" title={cand}>
                          {candShort}
                        </th>
                      );
                    })}
                  </tr>
                </thead>
                <tbody>
                  {vote_matrix.map((row, rIdx) => {
                    const evalShort = row.evaluator.split('/')[1] || row.evaluator;
                    return (
                      <tr key={rIdx}>
                        <td className="evaluator-name" title={row.evaluator}>
                          {evalShort}
                        </td>
                        {candidates.map((cand, cIdx) => {
                          const rank = row.ranks?.[cand] ?? '-';
                          const isTop = rank === 1;
                          return (
                            <td
                              key={cIdx}
                              className={`rank-cell ${isTop ? 'rank-top-cell' : ''}`}
                            >
                              <span className={`rank-tag ${isTop ? 'tag-gold' : ''}`}>
                                {rank === 1 ? '🥇 #1' : `#${rank}`}
                              </span>
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
