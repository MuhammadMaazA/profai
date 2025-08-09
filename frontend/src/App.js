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
    setError('');
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      
      const chunks = [];
      
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/wav' });
        await sendVoiceMessage(audioBlob);
        
        // Stop all tracks to release the microphone
        stream.getTracks().forEach(track => track.stop());
        setMediaRecorder(null);
      };

      setMediaRecorder(recorder);
      recorder.start();
      setIsRecording(true);
      
    } catch (err) {
      setError('Failed to access microphone. Please make sure you have granted microphone permissions.');
      console.error('Error accessing microphone:', err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  const sendVoiceMessage = async (audioBlob) => {
    setIsLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'recording.wav');

      const response = await axios.post(`${API_BASE_URL}/voice-chat`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const { transcription, response: aiResponse, audio_url } = response.data;

      // Add user message (transcription)
      setMessages(prev => [...prev, {
        type: 'user',
        content: transcription,
        audioUrl: null
      }]);

      // Add AI response
      setMessages(prev => [...prev, {
        type: 'ai',
        content: aiResponse,
        audioUrl: audio_url ? `${API_BASE_URL}${audio_url}` : null
      }]);

      // Auto-play the audio response
      if (audio_url) {
        const audio = new Audio(`${API_BASE_URL}${audio_url}`);
        audio.play().catch(err => {
          console.log('Auto-play failed (browser policy):', err);
        });
      }

    } catch (err) {
      console.error('Error sending voice message:', err);
      setError(err.response?.data?.detail || 'Failed to process voice message. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const sendTextMessage = async () => {
    if (!textInput.trim()) return;

    const userMessage = textInput.trim();
    setTextInput('');
    setIsLoading(true);
    setError('');

    // Add user message immediately
    setMessages(prev => [...prev, {
      type: 'user',
      content: userMessage,
      audioUrl: null
    }]);

    try {
      const response = await axios.post(`${API_BASE_URL}/ask`, {
        text: userMessage,
        emotion: 'friendly',
        play_audio: false
      });

      const { answer, audio_path } = response.data;

      // Add AI response
      setMessages(prev => [...prev, {
        type: 'ai',
        content: answer,
        audioUrl: audio_path ? `${API_BASE_URL}/audio/${audio_path}` : null
      }]);

      // Auto-play the audio response
      if (audio_path) {
        const audio = new Audio(`${API_BASE_URL}/audio/${audio_path}`);
        audio.play().catch(err => {
          console.log('Auto-play failed (browser policy):', err);
        });
      }

    } catch (err) {
      console.error('Error sending text message:', err);
      setError(err.response?.data?.detail || 'Failed to get response. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendTextMessage();
    }
  };

  return (
    <div className="app">
      <div className="header">
        <h1>🎓 ProfAI</h1>
        <p>Your AI Tutor with Voice Chat</p>
      </div>

      <div className="chat-container">
        <div className="chat-messages">
          {messages.map((message, index) => (
            <div key={index} className={`message ${message.type}`}>
              <div className="message-content">
                {message.content}
                {message.audioUrl && (
                  <div className="audio-indicator">
                    🔊 Audio response available
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="loading">
              <div className="loading-spinner"></div>
              <span>Processing...</span>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {error && <div className="error">{error}</div>}

        <div className="voice-controls">
          {/* Voice Recording Button */}
          <button
            className={`recording-button ${isRecording ? 'recording' : ''}`}
            onClick={isRecording ? stopRecording : startRecording}
            disabled={isLoading}
          >
            {isRecording ? <MicOff size={32} /> : <Mic size={32} />}
          </button>
          
          <div className="status">
            {isRecording 
              ? "🎙️ Recording... Click to stop" 
              : "🎤 Click to start voice chat"
            }
          </div>

          {/* Text Input Section */}
          <div className="text-input-section">
            <input
              type="text"
              className="text-input"
              placeholder="Or type your question here..."
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
            />
            <button
              className="send-button"
              onClick={sendTextMessage}
              disabled={isLoading || !textInput.trim()}
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
