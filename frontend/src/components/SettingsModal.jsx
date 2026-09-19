import { useState, useEffect } from 'react';
import './SettingsModal.css';

export default function SettingsModal({
  isOpen,
  onClose,
  currentSettings,
  availableModels,
  availablePersonas,
  onSaveSettings,
}) {
  const [councilModels, setCouncilModels] = useState([]);
  const [chairmanModel, setChairmanModel] = useState('');
  const [persona, setPersona] = useState('strict_truth');
  const [customModelId, setCustomModelId] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState('all');
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (currentSettings) {
      setCouncilModels(currentSettings.council_models || []);
      setChairmanModel(currentSettings.chairman_model || '');
      setPersona(currentSettings.persona || 'strict_truth');
    }
  }, [currentSettings, isOpen]);

  if (!isOpen) return null;

  // Preset Configurations
  const presets = [
    {
      name: '🆓 Free Tier Council',
      models: [
        'deepseek/deepseek-v4-flash-0731:free',
        'nvidia/nemotron-3.5-lightning:free',
        'liquid/lfm-2.5-2.6b:free',
        'nex-agi/nex-n2.5-pro:free',
      ],
      chairman: 'deepseek/deepseek-v4-flash-0731:free',
    },
    {
      name: '⚡ High-Speed Council',
      models: [
        'deepseek/deepseek-v4-flash-0731:free',
        'google/gemma-4-26b-a4b-it:free',
        'qwen/qwen3.8-27b:free',
        'z-ai/glm-5.2:free',
      ],
      chairman: 'google/gemma-4-26b-a4b-it:free',
    },
    {
      name: '🧠 Frontier Giants (Paid)',
      models: [
        'openai/gpt-4o',
        'anthropic/claude-3.7-sonnet',
        'google/gemini-2.5-pro',
        'deepseek/deepseek-r1',
      ],
      chairman: 'anthropic/claude-3.7-sonnet',
    },
  ];

  const applyPreset = (preset) => {
    setCouncilModels(preset.models);
    setChairmanModel(preset.chairman);
  };

  const handleAddModel = (modelId) => {
    if (!modelId || !modelId.trim()) return;
    const cleanId = modelId.trim();
    if (!councilModels.includes(cleanId)) {
      const updated = [...councilModels, cleanId];
      setCouncilModels(updated);
      if (!chairmanModel) {
        setChairmanModel(cleanId);
      }
    }
    setCustomModelId('');
  };

  const handleRemoveModel = (modelId) => {
    if (councilModels.length <= 1) {
      alert('You must have at least 1 model in the Council.');
      return;
    }
    const updated = councilModels.filter((m) => m !== modelId);
    setCouncilModels(updated);
    if (chairmanModel === modelId) {
      setChairmanModel(updated[0]);
    }
  };

  const handleSave = async () => {
    if (councilModels.length === 0) {
      alert('Please select at least 1 model for the council.');
      return;
    }
    const finalChairman = chairmanModel && councilModels.includes(chairmanModel)
      ? chairmanModel
      : councilModels[0];

    const newSettings = {
      council_models: councilModels,
      chairman_model: finalChairman,
      persona: persona || 'strict_truth',
    };

    await onSaveSettings(newSettings);
    setSaveSuccess(true);
    setTimeout(() => {
      setSaveSuccess(false);
      onClose();
    }, 600);
  };

  const filteredCatalog = availableModels.filter((m) => {
    const matchesSearch =
      m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.provider.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory =
      filterCategory === 'all' ||
      (filterCategory === 'free' && m.is_free) ||
      (filterCategory === 'paid' && !m.is_free);
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="settings-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div>
            <h2>🏛️ Council & Persona Settings</h2>
            <p className="modal-subtitle">
              Configure deliberation personas, active council models, and chairman synthesis.
            </p>
          </div>
          <button className="close-btn" onClick={onClose} title="Close settings">
            ✕
          </button>
        </div>

        <div className="modal-body">
          {/* Persona Selection Section */}
          {availablePersonas && availablePersonas.length > 0 && (
            <div className="settings-section">
              <h4 className="section-title">🎭 Specialized Deliberation Persona</h4>
              <p className="section-desc">
                Select the analytical framework, criteria, and tone used by the council models during deliberation.
              </p>
              <div className="persona-grid">
                {availablePersonas.map((p) => {
                  const isSelected = p.id === persona;
                  return (
                    <div
                      key={p.id}
                      className={`persona-card ${isSelected ? 'persona-card-active' : ''}`}
                      onClick={() => setPersona(p.id)}
                    >
                      <div className="persona-card-header">
                        <span className="persona-card-icon">{p.icon}</span>
                        <div className="persona-card-title-col">
                          <span className="persona-card-name">{p.name}</span>
                          <span className="persona-card-badge">{p.badge}</span>
                        </div>
                        {isSelected && <span className="persona-check">✓</span>}
                      </div>
                      <p className="persona-card-desc">{p.description}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Presets */}
          <div className="settings-section">
            <h4 className="section-title">⚡ Quick Presets</h4>
            <div className="preset-buttons">
              {presets.map((preset, idx) => (
                <button
                  key={idx}
                  className="preset-btn"
                  onClick={() => applyPreset(preset)}
                >
                  {preset.name}
                </button>
              ))}
            </div>
          </div>

          {/* Active Council Models */}
          <div className="settings-section">
            <h4 className="section-title">
              Active Council Members ({councilModels.length})
              <span className="section-hint"> — Click 👑 to set the synthesizing Chairman</span>
            </h4>

            <div className="active-models-list">
              {councilModels.map((modelId) => {
                const isChairman = modelId === chairmanModel;
                return (
                  <div
                    key={modelId}
                    className={`active-model-card ${isChairman ? 'is-chairman' : ''}`}
                  >
                    <div className="active-model-info">
                      <span className="model-slug">{modelId}</span>
                      {isChairman && <span className="chairman-badge">👑 Chairman</span>}
                    </div>

                    <div className="active-model-actions">
                      <button
                        className={`chairman-select-btn ${isChairman ? 'active' : ''}`}
                        onClick={() => setChairmanModel(modelId)}
                        title="Set this model as Chairman"
                      >
                        {isChairman ? '👑 Selected Chairman' : 'Make Chairman'}
                      </button>

                      <button
                        className="remove-model-btn"
                        onClick={() => handleRemoveModel(modelId)}
                        title="Remove from council"
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Model Catalog / Add Models */}
          <div className="settings-section">
            <h4 className="section-title">➕ Add Models to Council</h4>

            {/* Custom Model Input */}
            <div className="custom-input-group">
              <input
                type="text"
                placeholder="Enter custom OpenRouter model slug (e.g. meta-llama/llama-3.3-70b-instruct)"
                value={customModelId}
                onChange={(e) => setCustomModelId(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleAddModel(customModelId);
                }}
              />
              <button
                className="add-custom-btn"
                onClick={() => handleAddModel(customModelId)}
                disabled={!customModelId.trim()}
              >
                + Add Custom
              </button>
            </div>

            {/* Search and Filters */}
            <div className="catalog-filters">
              <input
                type="text"
                className="search-input"
                placeholder="Search models..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <div className="filter-pills">
                <button
                  className={`pill ${filterCategory === 'all' ? 'active' : ''}`}
                  onClick={() => setFilterCategory('all')}
                >
                  All
                </button>
                <button
                  className={`pill ${filterCategory === 'free' ? 'active' : ''}`}
                  onClick={() => setFilterCategory('free')}
                >
                  🆓 Free Only
                </button>
                <button
                  className={`pill ${filterCategory === 'paid' ? 'active' : ''}`}
                  onClick={() => setFilterCategory('paid')}
                >
                  🧠 Frontier/Paid
                </button>
              </div>
            </div>

            {/* Catalog Grid */}
            <div className="model-catalog-grid">
              {filteredCatalog.map((m) => {
                const isSelected = councilModels.includes(m.id);
                return (
                  <div
                    key={m.id}
                    className={`catalog-card ${isSelected ? 'already-selected' : ''}`}
                  >
                    <div className="card-top">
                      <span className="card-name">{m.name}</span>
                      <span className={`tag ${m.is_free ? 'tag-free' : 'tag-paid'}`}>
                        {m.is_free ? 'FREE' : 'PAID'}
                      </span>
                    </div>
                    <span className="card-id">{m.id}</span>
                    <p className="card-desc">{m.description}</p>
                    <button
                      className={`catalog-add-btn ${isSelected ? 'added' : ''}`}
                      onClick={() =>
                        isSelected ? handleRemoveModel(m.id) : handleAddModel(m.id)
                      }
                    >
                      {isSelected ? '✓ In Council (Click to Remove)' : '+ Add to Council'}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button
            className={`btn-primary ${saveSuccess ? 'btn-success' : ''}`}
            onClick={handleSave}
          >
            {saveSuccess ? '✓ Saved Successfully!' : 'Save Council Configuration'}
          </button>
        </div>
      </div>
    </div>
  );
}
