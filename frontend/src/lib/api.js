import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const chatWithAgent = async (query, sessionId) => {
  const response = await api.post('/api/v2/chat', {
    query,
    session_id: sessionId,
  });
  return response.data;
};

/**
 * Stream chat responses in real-time using Server-Sent Events
 * 
 * @param {string} query - The user's question
 * @param {string} sessionId - Session ID for conversation continuity
 * @param {Object} callbacks - Event handlers
 * @param {Function} callbacks.onToken - Called for each token: (content) => void
 * @param {Function} callbacks.onStepStart - Called when step starts: (step) => void
 * @param {Function} callbacks.onPlanComplete - Called when plan is ready: (plan) => void
 * @param {Function} callbacks.onToolStart - Called when tool starts: (toolName) => void
 * @param {Function} callbacks.onToolEnd - Called when tool ends: (toolName) => void
 * @param {Function} callbacks.onComplete - Called on completion: (sessionId, fullAnswer) => void
 * @param {Function} callbacks.onError - Called on error: (error) => void
 * @returns {Promise<void>}
 */
export const chatWithAgentStreaming = async (query, sessionId, callbacks) => {
  const {
    onToken = () => {},
    onStepStart = () => {},
    onPlanComplete = () => {},
    onToolStart = () => {},
    onToolEnd = () => {},
    onComplete = () => {},
    onError = () => {}
  } = callbacks;

  try {
    // Use fetch API for streaming (axios doesn't support SSE well)
    const response = await fetch(`${API_BASE_URL}/api/v2/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        break;
      }

      // Decode chunk and add to buffer
      buffer += decoder.decode(value, { stream: true });

      // Process complete lines (SSE format: "data: {...}\n\n")
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const event = JSON.parse(line.slice(6));

            switch (event.type) {
              case 'token':
                onToken(event.content);
                break;
              
              case 'step_start':
                onStepStart(event.step);
                break;
              
              case 'plan_complete':
                onPlanComplete(event.plan);
                break;
              
              case 'tool_start':
                onToolStart(event.tool);
                break;
              
              case 'tool_end':
                onToolEnd(event.tool);
                break;
              
              case 'complete':
                onComplete(event.session_id, event.answer);
                break;
              
              case 'error':
                onError(new Error(event.message));
                break;
            }
          } catch (parseError) {
            console.error('Error parsing SSE event:', parseError, line);
          }
        }
      }
    }
  } catch (error) {
    console.error('Streaming error:', error);
    onError(error);
  }
};

export const getCompanies = async () => {
  const response = await api.get('/api/companies')
  return response.data
}

export const getHealth = async () => {
  const response = await api.get('/api/health')
  return response.data
}

export const processCompany = async (ticker, filing_type = '10-K') => {
  const response = await api.post(`/api/companies/${ticker}/process`, {
    filing_type,
  })
  return response.data
}

export default api
