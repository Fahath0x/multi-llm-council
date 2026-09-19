/**
 * API client for the LLM Council backend.
 */

const API_BASE = 'http://localhost:8001';

export const api = {
  /**
   * List all conversations.
   */
  async listConversations() {
    const response = await fetch(`${API_BASE}/api/conversations`);
    if (!response.ok) {
      throw new Error('Failed to list conversations');
    }
    return response.json();
  },

  /**
   * Create a new conversation.
   */
  async createConversation() {
    const response = await fetch(`${API_BASE}/api/conversations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({}),
    });
    if (!response.ok) {
      throw new Error('Failed to create conversation');
    }
    return response.json();
  },

  /**
   * Get a specific conversation.
   */
  async getConversation(conversationId) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}`
    );
    if (!response.ok) {
      throw new Error('Failed to get conversation');
    }
    return response.json();
  },

  /**
   * Get current council settings.
   */
  async getSettings() {
    const response = await fetch(`${API_BASE}/api/settings`);
    if (!response.ok) {
      throw new Error('Failed to get council settings');
    }
    return response.json();
  },

  /**
   * Update council settings.
   */
  async updateSettings(settings) {
    const response = await fetch(`${API_BASE}/api/settings`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(settings),
    });
    if (!response.ok) {
      throw new Error('Failed to update council settings');
    }
    return response.json();
  },

  /**
   * List available curated models.
   */
  async getAvailableModels() {
    const response = await fetch(`${API_BASE}/api/models`);
    if (!response.ok) {
      throw new Error('Failed to list available models');
    }
    return response.json();
  },

  /**
   * List specialized council personas.
   */
  async getPersonas() {
    const response = await fetch(`${API_BASE}/api/personas`);
    if (!response.ok) {
      throw new Error('Failed to list personas');
    }
    return response.json();
  },

  /**
   * Delete a conversation permanently.
   */
  async deleteConversation(conversationId) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}`,
      { method: 'DELETE' }
    );
    if (!response.ok && response.status !== 404) {
      throw new Error('Failed to delete conversation');
    }
    return true;
  },

  /**
   * Send a message in a conversation.
   */
  async sendMessage(conversationId, content, options = {}) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/message`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content,
          council_models: options.council_models,
          chairman_model: options.chairman_model,
          persona: options.persona,
        }),
      }
    );
    if (!response.ok) {
      throw new Error('Failed to send message');
    }
    return response.json();
  },

  /**
   * Send a message and receive streaming updates.
   * @param {string} conversationId - The conversation ID
   * @param {string} content - The message content
   * @param {object} options - Optional { council_models, chairman_model, persona }
   * @param {function} onEvent - Callback function for each event: (eventType, data) => void
   * @returns {Promise<void>}
   */
  async sendMessageStream(conversationId, content, options = {}, onEvent) {
    // Handle backwards compatibility if onEvent passed as 3rd param
    let actualOptions = options;
    let actualOnEvent = onEvent;
    if (typeof options === 'function') {
      actualOnEvent = options;
      actualOptions = {};
    }

    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/message/stream`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content,
          council_models: actualOptions.council_models,
          chairman_model: actualOptions.chairman_model,
          persona: actualOptions.persona,
        }),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to send message');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let lineBuffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      lineBuffer += decoder.decode(value, { stream: true });
      const lines = lineBuffer.split('\n');
      // The last element is either an incomplete line or empty string if line ended with \n
      lineBuffer = lines.pop() || '';

      for (const rawLine of lines) {
        const line = rawLine.trim();
        if (line.startsWith('data:')) {
          const data = line.slice(5).trim();
          if (data) {
            try {
              const event = JSON.parse(data);
              if (actualOnEvent) {
                actualOnEvent(event.type, event);
              }
            } catch (e) {
              console.error('Failed to parse SSE event:', e, 'Raw:', data);
            }
          }
        }
      }
    }
  },
};
