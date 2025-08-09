import React, { useState, useRef, useEffect } from 'react';
import './App_enhanced.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcription, setTranscription] = useState('');
  const [response, setResponse] = useState('');
  const [error, setError] = useState('');
  const [textInput, setTextInput] = useState('');
  
  // Educational features state
  const [curriculum, setCurriculum] = useState({});
  const [currentModule, setCurrentModule] = useState(null);
  const [learningProgress, setLearningProgress] = useState({});
  const [emotionalContext, setEmotionalContext] = useState(null);
  const [showCurriculum, setShowCurriculum] = useState(false);
  const [userId] = useState('user_' + Date.now()); // Simple user ID for demo
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioRef = useRef(null);

  // Load curriculum on component mount
  useEffect(() => {
    fetchCurriculum();
    fetchProgress();
  }, []);

  const fetchCurriculum = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/curriculum`);
      const data = await response.json();
      setCurriculum(data.modules);
    } catch (error) {
      console.error('Error fetching curriculum:', error);
    }
  };

  const fetchProgress = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/progress/${userId}`);
      const data = await response.json();
      setLearningProgress(data);
      if (data.current_module) {
        setCurrentModule(data.current_module);
      }
    } catch (error) {
      console.error('Error fetching progress:', error);
    }
  };

  const startModule = async (moduleId) => {
    try {
      setIsProcessing(true);
      const response = await fetch(`${API_BASE_URL}/start-module`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          module_id: moduleId
        })
      });
      
      const data = await response.json();
      setCurrentModule(moduleId);
      setResponse(data.message || 'Module started successfully!');
      await fetchProgress(); // Refresh progress
    } catch (error) {
      setError('Failed to start module: ' + error.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      audioChunksRef.current = [];
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm;codecs=opus' });
        sendVoiceMessage(audioBlob);
        
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorderRef.current.start();
      setIsRecording(true);
      setError('');
    } catch (error) {
      setError('Failed to access microphone: ' + error.message);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const sendVoiceMessage = async (audioBlob) => {
    setIsProcessing(true);
    
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'voice_message.webm');
    formData.append('user_id', userId);
    
    try {
      const response = await fetch(`${API_BASE_URL}/voice-chat-enhanced`, {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setTranscription(data.transcription);
      setResponse(data.response);
      setEmotionalContext(data.educational_context);
      
      if (data.audio_url) {
        const audio = new Audio(`${API_BASE_URL}${data.audio_url}`);
        audioRef.current = audio;
        
        // Auto-play the response
        try {
          await audio.play();
        } catch (playError) {
          console.log('Auto-play failed, user interaction required');
        }
      }
      
      // Refresh progress after interaction
      await fetchProgress();
      
    } catch (error) {
      setError('Failed to process voice message: ' + error.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const sendTextMessage = async () => {
    if (!textInput.trim()) return;
    
    setIsProcessing(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: textInput,
          play_audio: true,
          user_id: userId
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setResponse(data.response);
      setEmotionalContext(data.educational_context);
      
      if (data.audio_url) {
        const audio = new Audio(`${API_BASE_URL}${data.audio_url}`);
        audioRef.current = audio;
        
        try {
          await audio.play();
        } catch (playError) {
          console.log('Auto-play failed');
        }
      }
      
      setTextInput('');
      await fetchProgress();
      
    } catch (error) {
      setError('Failed to send message: ' + error.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const getEmotionIcon = (emotion) => {
    switch (emotion?.toLowerCase()) {
      case 'confused': return '😕';
      case 'frustrated': return '😤';
      case 'excited': return '😃';
      case 'confident': return '😎';
      case 'curious': return '🤔';
      default: return '😊';
    }
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty?.toLowerCase()) {
      case 'beginner': return '#4CAF50';
      case 'intermediate': return '#FF9800';
      case 'advanced': return '#F44336';
      default: return '#2196F3';
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🎓 ProfAI - AI Professor with Emotional Intelligence</h1>
        <p className="subtitle">Voice-driven AI education with personalized learning</p>
      </header>

      <main className="main-content">
        {/* Educational Dashboard */}
        <div className="education-panel">
          <div className="current-status">
            <h3>Learning Status</h3>
            {currentModule && (
              <div className="current-module">
                <span className="module-label">Current Module:</span>
                <span className="module-name">{curriculum[currentModule]?.title || currentModule}</span>
              </div>
            )}
            {emotionalContext && (
              <div className="emotional-state">
                <span className="emotion-icon">{getEmotionIcon(emotionalContext.detected_emotion)}</span>
                <span className="emotion-text">
                  {emotionalContext.detected_emotion} 
                  {emotionalContext.confidence_level && ` (${emotionalContext.confidence_level}% confidence)`}
                </span>
              </div>
            )}
          </div>

          <button 
            className="curriculum-toggle"
            onClick={() => setShowCurriculum(!showCurriculum)}
          >
            {showCurriculum ? '📚 Hide Curriculum' : '📚 Show Curriculum'}
          </button>
        </div>

        {/* Curriculum Panel */}
        {showCurriculum && (
          <div className="curriculum-panel">
            <h3>Available Learning Modules</h3>
            <div className="modules-grid">
              {Object.entries(curriculum).map(([moduleId, module]) => (
                <div key={moduleId} className="module-card">
                  <div className="module-header">
                    <h4>{module.title}</h4>
                    <span 
                      className="difficulty-badge"
                      style={{ backgroundColor: getDifficultyColor(module.difficulty) }}
                    >
                      {module.difficulty}
                    </span>
                  </div>
                  <p className="module-description">{module.description}</p>
                  <div className="module-stats">
                    <span>📚 {module.theory_count} topics</span>
                    <span>🛠️ {module.project_count} projects</span>
                    <span>⏱️ {module.estimated_time}</span>
                  </div>
                  {module.prerequisites && module.prerequisites.length > 0 && (
                    <div className="prerequisites">
                      <strong>Prerequisites:</strong> {module.prerequisites.join(', ')}
                    </div>
                  )}
                  <button 
                    className="start-module-btn"
                    onClick={() => startModule(moduleId)}
                    disabled={isProcessing || currentModule === moduleId}
                  >
                    {currentModule === moduleId ? '✅ Active' : '🚀 Start Module'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Chat Interface */}
        <div className="chat-section">
          <div className="input-section">
            <h3>Chat with ProfAI</h3>
            
            {/* Voice Input */}
            <div className="voice-controls">
              <button 
                className={`record-btn ${isRecording ? 'recording' : ''}`}
                onClick={isRecording ? stopRecording : startRecording}
                disabled={isProcessing}
              >
                {isRecording ? '🔴 Stop Recording' : '🎤 Start Recording'}
              </button>
              {isRecording && <div className="recording-indicator">🎵 Recording...</div>}
            </div>

            {/* Text Input */}
            <div className="text-input-section">
              <textarea
                className="text-input"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Type your question or message..."
                rows="3"
                disabled={isProcessing}
              />
              <button 
                className="send-btn"
                onClick={sendTextMessage}
                disabled={isProcessing || !textInput.trim()}
              >
                💬 Send Message
              </button>
            </div>
          </div>

          {/* Processing Indicator */}
          {isProcessing && (
            <div className="processing-indicator">
              <div className="spinner"></div>
              <span>ProfAI is thinking...</span>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="error-message">
              ❌ {error}
            </div>
          )}

          {/* Results Display */}
          <div className="results-section">
            {transcription && (
              <div className="transcription-result">
                <h4>📝 You said:</h4>
                <p>{transcription}</p>
              </div>
            )}

            {response && (
              <div className="response-result">
                <h4>🎓 ProfAI responds:</h4>
                <p>{response}</p>
              </div>
            )}

            {emotionalContext?.suggested_action && (
              <div className="suggestion-panel">
                <h4>💡 Suggested Next Action:</h4>
                <p>{emotionalContext.suggested_action}</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
