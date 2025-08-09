import React, { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Send } from 'lucide-react';
import axios from 'axios';
import './index.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([
    {
      type: 'ai',
      content: "Hello! I'm ProfAI, your AI tutor. I can help you learn about any topic. You can either type your questions or use voice chat by clicking the microphone button below.",
      audioUrl: null
    }
  ]);
  const [isRecording, setIsRecording] = useState(false);
  const [textInput, setTextInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Start recording - create new recorder each time
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
                  <div className="audio-player">
                    <audio controls>
                      <source src={message.audioUrl} type="audio/mpeg" />
                      Your browser does not support the audio element.
                    </audio>
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
