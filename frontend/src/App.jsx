import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import SettingsModal from './components/SettingsModal';
import { api } from './api';
import './App.css';

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Settings State
  const [currentSettings, setCurrentSettings] = useState({
    council_models: [
      'deepseek/deepseek-v4-flash-0731:free',
      'nvidia/nemotron-3.5-lightning:free',
      'liquid/lfm-2.5-2.6b:free',
      'nex-agi/nex-n2.5-pro:free',
    ],
    chairman_model: 'deepseek/deepseek-v4-flash-0731:free',
    persona: 'strict_truth',
  });
  const [availableModels, setAvailableModels] = useState([]);
  const [availablePersonas, setAvailablePersonas] = useState([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const loadConversations = async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const loadSettings = async () => {
    try {
      const settings = await api.getSettings();
      setCurrentSettings(settings);
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const loadAvailableModels = async () => {
    try {
      const models = await api.getAvailableModels();
      setAvailableModels(models);
    } catch (error) {
      console.error('Failed to load available models:', error);
    }
  };

  const loadPersonas = async () => {
    try {
      const personas = await api.getPersonas();
      setAvailablePersonas(personas);
    } catch (error) {
      console.error('Failed to load personas:', error);
    }
  };

  const loadConversation = async (id) => {
    try {
      const conv = await api.getConversation(id);
      setCurrentConversation(conv);
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  // Load conversations, settings, models, and personas on mount
  useEffect(() => {
    loadConversations();
    loadSettings();
    loadAvailableModels();
    loadPersonas();
  }, []);

  // Load conversation details when selected
  useEffect(() => {
    if (currentConversationId) {
      loadConversation(currentConversationId);
    }
  }, [currentConversationId]);

  const handleSaveSettings = async (newSettings) => {
    try {
      const saved = await api.updateSettings(newSettings);
      setCurrentSettings(saved);
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  const handleSelectPersona = async (personaId) => {
    const updated = { ...currentSettings, persona: personaId };
    setCurrentSettings(updated);
    try {
      await api.updateSettings(updated);
    } catch (error) {
      console.error('Failed to update persona:', error);
    }
  };

  const handleNewConversation = async () => {
    try {
      const newConv = await api.createConversation();
      setConversations([
        { id: newConv.id, created_at: newConv.created_at, message_count: 0 },
        ...conversations,
      ]);
      setCurrentConversationId(newConv.id);
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  const handleSelectConversation = (id) => {
    setCurrentConversationId(id);
  };

  const handleDeleteConversation = async (id) => {
    try {
      await api.deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (currentConversationId === id) {
        setCurrentConversationId(null);
        setCurrentConversation(null);
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };

  const handleSendMessage = async (content) => {
    if (!currentConversationId) return;

    setIsLoading(true);
    try {
      // Optimistically add user message and assistant loading state in ONE atomic update
      const userMessage = { role: 'user', content };
      const assistantMessage = {
        role: 'assistant',
        stage1: null,
        stage2: null,
        stage3: null,
        metadata: {
          persona: availablePersonas.find((p) => p.id === (currentSettings.persona || 'strict_truth')),
        },
        loading: {
          stage1: true,
          stage2: false,
          stage3: false,
        },
      };

      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...(prev?.messages || []), userMessage, assistantMessage],
      }));

      // Pass active council, chairman, and persona settings
      const options = {
        council_models: currentSettings?.council_models,
        chairman_model: currentSettings?.chairman_model,
        persona: currentSettings?.persona || 'strict_truth',
      };

      // Send message with streaming
      await api.sendMessageStream(
        currentConversationId,
        content,
        options,
        (eventType, event) => {
          switch (eventType) {
            case 'persona_info':
              setCurrentConversation((prev) => {
                if (!prev || !prev.messages.length) return prev;
                const messages = [...prev.messages];
                const lastIdx = messages.length - 1;
                messages[lastIdx] = {
                  ...messages[lastIdx],
                  metadata: {
                    ...(messages[lastIdx].metadata || {}),
                    persona: event.persona,
                  },
                };
                return { ...prev, messages };
              });
              break;
            case 'stage1_start':
              setCurrentConversation((prev) => {
                if (!prev || !prev.messages.length) return prev;
                const messages = [...prev.messages];
                const lastIdx = messages.length - 1;
                const initialStage1 = (event.models || []).map((m) => ({
                  model: m,
                  response: '',
                }));
                messages[lastIdx] = {
                  ...messages[lastIdx],
                  stage1: initialStage1,
                  loading: { ...messages[lastIdx].loading, stage1: true, stage2: false, stage3: false },
                };
                return { ...prev, messages };
              });
              break;

            case 'stage1_token':
              setCurrentConversation((prev) => {
                if (!prev || !prev.messages.length) return prev;
                const messages = [...prev.messages];
                const lastIdx = messages.length - 1;
                const currentMsg = messages[lastIdx];
                const stage1List = Array.isArray(currentMsg.stage1) ? [...currentMsg.stage1] : [];
                const modelIdx = stage1List.findIndex((item) => item.model === event.model);
                if (modelIdx >= 0) {
                  stage1List[modelIdx] = {
                    ...stage1List[modelIdx],
                    response: (stage1List[modelIdx].response || '') + event.token,
                  };
                } else {
                  stage1List.push({
                    model: event.model,
                    response: event.token,
                  });
                }
                messages[lastIdx] = {
                  ...currentMsg,
                  stage1: stage1List,
                };
                return { ...prev, messages };
              });
              break;

            case 'stage1_complete':
              setCurrentConversation((prev) => {
                if (!prev || !prev.messages.length) return prev;
                const messages = [...prev.messages];
                const lastIdx = messages.length - 1;
                messages[lastIdx] = {
                  ...messages[lastIdx],
                  stage1: event.data,
                  loading: { ...messages[lastIdx].loading, stage1: false, stage2: true },
                };
                return { ...prev, messages };
              });
              break;

            case 'stage2_start':
              setCurrentConversation((prev) => {
                if (!prev || !prev.messages.length) return prev;
                const messages = [...prev.messages];
                const lastIdx = messages.length - 1;
                const initialStage2 = (event.models || []).map((m) => ({
                  model: m,
                  ranking: '',
                }));
                messages[lastIdx] = {
                  ...messages[lastIdx],
                  stage2: initialStage2,
                  loading: { ...messages[lastIdx].loading, stage2: true },
                };
                return { ...prev, messages };
              });
              break;

            case 'stage2_token':
              setCurrentConversation((prev) => {
                if (!prev || !prev.messages.length) return prev;
                const messages = [...prev.messages];
                const lastIdx = messages.length - 1;
                const currentMsg = messages[lastIdx];
                const stage2List = Array.isArray(currentMsg.stage2) ? [...currentMsg.stage2] : [];
                const modelIdx = stage2List.findIndex((item) => item.model === event.model);
                if (modelIdx >= 0) {
                  stage2List[modelIdx] = {
                    ...stage2List[modelIdx],
                    ranking: (stage2List[modelIdx].ranking || '') + event.token,
                  };
                } else {
                  stage2List.push({
                    model: event.model,
                    ranking: event.token,
                  });
                }
                messages[lastIdx] = {
                  ...currentMsg,
                  stage2: stage2List,
                };
                return { ...prev, messages };
              });
              break;

            case 'stage2_complete':
              setCurrentConversation((prev) => {
                if (!prev || !prev.messages.length) return prev;
                const messages = [...prev.messages];
                const lastIdx = messages.length - 1;
                messages[lastIdx] = {
                  ...messages[lastIdx],
                  stage2: event.data,
                  metadata: event.metadata,
                  loading: { ...messages[lastIdx].loading, stage2: false, stage3: true },
                };
                return { ...prev, messages };
              });
              break;

            case 'stage3_start':
              setCurrentConversation((prev) => {
                if (!prev || !prev.messages.length) return prev;
                const messages = [...prev.messages];
                const lastIdx = messages.length - 1;
                messages[lastIdx] = {
                  ...messages[lastIdx],
                  stage3: {
                    model: event.chairman || 'Chairman',
                    response: '',
                    streaming: true,
                  },
                  loading: { ...messages[lastIdx].loading, stage3: true },
                };
                return { ...prev, messages };
              });
              break;

            case 'stage3_token':
              setCurrentConversation((prev) => {
                if (!prev || !prev.messages.length) return prev;
                const messages = [...prev.messages];
                const lastIdx = messages.length - 1;
                const currentMsg = messages[lastIdx];
                const currentStage3 = currentMsg.stage3 || {
                  model: 'Chairman',
                  response: '',
                  streaming: true,
                };
                messages[lastIdx] = {
                  ...currentMsg,
                  stage3: {
                    ...currentStage3,
                    response: (currentStage3.response || '') + event.token,
                    streaming: true,
                  },
                };
                return { ...prev, messages };
              });
              break;

            case 'stage3_complete':
              setCurrentConversation((prev) => {
                if (!prev || !prev.messages.length) return prev;
                const messages = [...prev.messages];
                const lastIdx = messages.length - 1;
                messages[lastIdx] = {
                  ...messages[lastIdx],
                  stage3: {
                    ...event.data,
                    streaming: false,
                  },
                  loading: { stage1: false, stage2: false, stage3: false },
                };
                return { ...prev, messages };
              });
              break;

            case 'title_complete':
              loadConversations();
              break;

            case 'complete':
              loadConversations();
              setIsLoading(false);
              break;

            case 'error':
              console.error('Stream error:', event.message);
              setIsLoading(false);
              break;

            default:
              console.log('Unknown event type:', eventType);
          }
        }
      );
    } catch (error) {
      console.error('Failed to send message:', error);
      // Remove optimistic messages on error
      setCurrentConversation((prev) => ({
        ...prev,
        messages: prev.messages.slice(0, -2),
      }));
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <Sidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
        currentSettings={currentSettings}
        availablePersonas={availablePersonas}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />
      <ChatInterface
        conversation={currentConversation}
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
        currentSettings={currentSettings}
        availablePersonas={availablePersonas}
        onSelectPersona={handleSelectPersona}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      {/* Dynamic Model, Chairman & Persona Selector Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        currentSettings={currentSettings}
        availableModels={availableModels}
        availablePersonas={availablePersonas}
        onSaveSettings={handleSaveSettings}
      />
    </div>
  );
}

export default App;
