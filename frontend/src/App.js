import React, { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Send, BookOpen, Code, Zap, Settings } from 'lucide-react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import './index.css';

const API_BASE_URL = 'http://localhost:8000';

// Learning paths and formats
const LEARNING_PATHS = {
  theory: { name: 'Theory', icon: BookOpen, description: 'AI fundamentals, algorithms, concepts' },
  tooling: { name: 'Tooling', icon: Code, description: 'Hands-on tools, coding, deployment' },
  hybrid: { name: 'Hybrid', icon: Zap, description: 'Theory + immediate application' }
};

const DELIVERY_FORMATS = {
  micro_learning: { name: 'Quick Lessons', description: '5-10 minute focused lessons' },
  deep_dive: { name: 'Deep Dive', description: 'Comprehensive tutorials' },
  audio_lessons: { name: 'Audio Lessons', description: 'Podcast-style learning' }
};

const LANGUAGES = {
  en: { name: 'English', flag: '🇺🇸' },
  es: { name: 'Español', flag: '🇪🇸' },
  fr: { name: 'Français', flag: '🇫🇷' },
  de: { name: 'Deutsch', flag: '🇩🇪' },
  it: { name: 'Italiano', flag: '🇮🇹' },
  pt: { name: 'Português', flag: '🇵🇹' },
  pl: { name: 'Polski', flag: '🇵🇱' },
  hi: { name: 'हिन्दी', flag: '🇮🇳' },
  ar: { name: 'العربية', flag: '🇸🇦' },
  zh: { name: '中文', flag: '🇨🇳' },
  ja: { name: '日本語', flag: '🇯🇵' },
  ko: { name: '한국어', flag: '🇰🇷' }
};

function App() {
  const [messages, setMessages] = useState([
    {
      type: 'ai',
      content: "Hello! I'm ProfAI, your specialized AI professor. I can teach AI theory, practical tooling, or both. Choose your learning path and let's start your AI journey!",
      audioUrl: 'loading', // Use 'loading' instead of null to show proper state
      emotion: null
    }
  ]);
  const [isRecording, setIsRecording] = useState(false);
  const [textInput, setTextInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const [showSettings, setShowSettings] = useState(false);
  const [showCurriculum, setShowCurriculum] = useState(false);
  const [learningPath, setLearningPath] = useState('hybrid');
  const [deliveryFormat, setDeliveryFormat] = useState('audio_lessons');
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [conversationHistory, setConversationHistory] = useState([]);
  const messagesEndRef = useRef(null);
  const audioChunksRef = useRef([]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Generate audio for welcome message on component mount
  useEffect(() => {
    const generateWelcomeAudio = async () => {
      try {
        const welcomeMessage = "Hello! I'm ProfAI, your specialized AI professor. I can teach AI theory, practical tooling, or both. Choose your learning path and let's start your AI journey!";
        const response = await axios.post(`${API_BASE_URL}/tts`, {
          text: welcomeMessage,
          play_audio: false,
          language: selectedLanguage
        });

        if (response.data.audio_path) {
          // Update the welcome message with audio
          setMessages(prev => prev.map((msg, idx) => 
            idx === 0 && msg.type === 'ai' && msg.audioUrl === 'loading'
              ? { ...msg, audioUrl: `${API_BASE_URL}/audio/${response.data.audio_path.split('/').pop()}` }
              : msg
          ));
        } else {
          // If no audio generated, mark as unavailable
          setTimeout(() => {
            setMessages(prev => prev.map((msg, idx) => 
              idx === 0 && msg.type === 'ai' && msg.audioUrl === 'loading'
                ? { ...msg, audioUrl: null }
                : msg
            ));
          }, 3000);
        }
      } catch (error) {
        console.error('Error generating welcome audio:', error);
        // Mark audio as unavailable after timeout
        setTimeout(() => {
          setMessages(prev => prev.map((msg, idx) => 
            idx === 0 && msg.type === 'ai' && msg.audioUrl === 'loading'
              ? { ...msg, audioUrl: null }
              : msg
          ));
        }, 3000);
      }
    };

    generateWelcomeAudio();
  }, []); // Empty dependency array means this runs once on mount

  const startRecording = async () => {
    setError('');
    
    // Always reinitialize for each recording session
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });
      
      // Use a simpler, more compatible format
      let options = {};
      if (MediaRecorder.isTypeSupported('audio/webm')) {
        options.mimeType = 'audio/webm';
      } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        options.mimeType = 'audio/mp4';
      }
      
      console.log('Creating new recorder with options:', options);
      
      const recorder = new MediaRecorder(stream, options);
      
      // Clear previous chunks
      audioChunksRef.current = [];
      setAudioChunks([]);
      
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          console.log('Received audio chunk:', event.data.size, 'bytes');
          audioChunksRef.current.push(event.data);
          setAudioChunks(prev => [...prev, event.data]);
        }
      };

      recorder.onstop = async () => {
        console.log('Recording stopped. Total chunks:', audioChunksRef.current.length);
        const mimeType = options.mimeType || 'audio/webm';
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        console.log('Created audio blob:', {
          type: audioBlob.type,
          size: audioBlob.size,
          chunks: audioChunksRef.current.length
        });
        
        if (audioBlob.size > 0) {
          await sendVoiceMessage(audioBlob);
        } else {
          setError('Recording failed - no audio data captured');
        }
        
        // Clear chunks for next recording
        audioChunksRef.current = [];
        setAudioChunks([]);
        
        // Stop all tracks to release the microphone
        stream.getTracks().forEach(track => track.stop());
        
        // Clear the recorder
        setMediaRecorder(null);
      };

      setMediaRecorder(recorder);
      
      console.log('Starting recording...');
      recorder.start(100); // Request data every 100ms
      setIsRecording(true);
      
    } catch (err) {
      setError('Failed to access microphone. Please make sure you have granted microphone permissions.');
      console.error('Error accessing microphone:', err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      console.log('Stopping recording...');
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  const sendVoiceMessage = async (audioBlob) => {
    setIsLoading(true);
    setError('');

    try {
      const formData = new FormData();
      // Get file extension based on blob type
      let filename = 'recording.webm';
      if (audioBlob.type.includes('mp4')) {
        filename = 'recording.mp4';
      } else if (audioBlob.type.includes('ogg')) {
        filename = 'recording.ogg';
      } else if (audioBlob.type.includes('wav')) {
        filename = 'recording.wav';
      }
      
      console.log('Sending audio file:', {
        filename,
        type: audioBlob.type,
        size: audioBlob.size
      });
      
      formData.append('audio_file', audioBlob, filename);

      const response = await axios.post(`${API_BASE_URL}/voice-chat?language=${selectedLanguage}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const { transcription, response: aiResponse, audio_url, detected_emotion } = response.data;

      console.log('Voice response data:', {
        transcription,
        aiResponse,
        audio_url,
        detected_emotion,
        emotionType: typeof detected_emotion
      });

      // Add user message (transcription)
      const userMessage = {
        type: 'user',
        content: transcription,
        audioUrl: null,
        emotion: detected_emotion
      };
      
      setMessages(prev => [...prev, userMessage]);
      setConversationHistory(prev => [...prev, transcription]);

      // Add AI response with loading audio state initially
      const aiMessage = {
        type: 'ai',
        content: aiResponse,
        audioUrl: 'loading', // Show loading state initially
        emotion: detected_emotion
      };
      
      setMessages(prev => [...prev, aiMessage]);
      setConversationHistory(prev => [...prev, aiResponse]);

      // If audio_url is available, update the message with the actual audio
      if (audio_url) {
        setTimeout(() => {
          setMessages(prev => prev.map((msg, idx) => 
            idx === prev.length - 1 && msg.type === 'ai' && msg.audioUrl === 'loading'
              ? { ...msg, audioUrl: `${API_BASE_URL}${audio_url}` }
              : msg
          ));
        }, 100); // Small delay to ensure message is rendered first
      } else {
        // If no audio URL, show unavailable after a short delay
        setTimeout(() => {
          setMessages(prev => prev.map((msg, idx) => 
            idx === prev.length - 1 && msg.type === 'ai' && msg.audioUrl === 'loading'
              ? { ...msg, audioUrl: null }
              : msg
          ));
        }, 2000); // Show loading for 2 seconds then show unavailable
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
      audioUrl: null,
      emotion: null
    }]);
    
    setConversationHistory(prev => [...prev, userMessage]);

    try {
      const response = await axios.post(`${API_BASE_URL}/ask`, {
        text: userMessage,
        emotion: 'friendly',
        play_audio: false,
        learning_path: learningPath,
        delivery_format: deliveryFormat,
        conversation_history: conversationHistory,
        language: selectedLanguage
      });

      const { answer, audio_path } = response.data;

      // Add AI response with loading audio state initially
      const aiMessage = {
        type: 'ai',
        content: answer,
        audioUrl: 'loading',
        emotion: null
      };
      
      setMessages(prev => [...prev, aiMessage]);
      setConversationHistory(prev => [...prev, answer]);

      // If audio_path is available, update the message with the actual audio
      if (audio_path) {
        setTimeout(() => {
          setMessages(prev => prev.map((msg, idx) => 
            idx === prev.length - 1 && msg.type === 'ai' && msg.audioUrl === 'loading'
              ? { ...msg, audioUrl: `${API_BASE_URL}/audio/${audio_path.split('/').pop()}` }
              : msg
          ));
        }, 100);
      } else {
        // If no audio path, show unavailable after a short delay
        setTimeout(() => {
          setMessages(prev => prev.map((msg, idx) => 
            idx === prev.length - 1 && msg.type === 'ai' && msg.audioUrl === 'loading'
              ? { ...msg, audioUrl: null }
              : msg
          ));
        }, 2000);
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

  // Curriculum browser component
  const CurriculumBrowser = () => {
    const [curriculum, setCurriculum] = useState(null);
    const [selectedSubject, setSelectedSubject] = useState('');
    const [loadingCurriculum, setLoadingCurriculum] = useState(false);

    const fetchCurriculum = async () => {
      setLoadingCurriculum(true);
      try {
        const response = await axios.get(`${API_BASE_URL}/curriculum`, {
          params: { 
            learning_path: learningPath,
            subject: selectedSubject || undefined
          }
        });
        
        console.log('Curriculum API Response:', response.data);
        
        // Ensure lessons and recommendations are always arrays
        const curriculumData = {
          ...response.data,
          lessons: Array.isArray(response.data.lessons) ? response.data.lessons : [],
          recommendations: Array.isArray(response.data.recommendations) ? response.data.recommendations : []
        };
        
        setCurriculum(curriculumData);
      } catch (err) {
        console.error('Error fetching curriculum:', err);
        setError('Failed to load curriculum');
      } finally {
        setLoadingCurriculum(false);
      }
    };

    const startLesson = async (lessonId) => {
      try {
        const response = await axios.post(`${API_BASE_URL}/lesson`, {
          lesson_id: lessonId,
          learning_path: learningPath,
          delivery_format: deliveryFormat
        });
        
        // Add lesson content as AI message
        setMessages(prev => [...prev, {
          type: 'ai',
          content: response.data.content,
          audioUrl: response.data.audio_path ? `${API_BASE_URL}/audio/${response.data.audio_path.split('/').pop()}` : null,
          emotion: null
        }]);
        
        setShowCurriculum(false);
      } catch (err) {
        console.error('Error starting lesson:', err);
        setError('Failed to start lesson');
      }
    };

    if (!curriculum) {
      return (
        <div className="curriculum-browser">
          <div className="curriculum-header">
            <h3>📚 Course Curriculum</h3>
            <button onClick={() => setShowCurriculum(false)}>✕</button>
          </div>
          <div className="curriculum-controls">
            <select 
              value={selectedSubject} 
              onChange={(e) => setSelectedSubject(e.target.value)}
              className="subject-select"
            >
              <option value="">All Subjects</option>
              <option value="machine_learning">Machine Learning</option>
              <option value="python">Python Programming</option>
              <option value="data_science">Data Science</option>
              <option value="statistics">Statistics</option>
              <option value="computer_science">Computer Science</option>
            </select>
            <button 
              onClick={fetchCurriculum} 
              disabled={loadingCurriculum}
              className="fetch-button"
            >
              {loadingCurriculum ? 'Loading...' : 'Load Curriculum'}
            </button>
          </div>
        </div>
      );
    }

    return (
      <div className="curriculum-browser">
        <div className="curriculum-header">
          <h3>📚 {curriculum.title || 'Course Curriculum'}</h3>
          <button onClick={() => setShowCurriculum(false)}>✕</button>
        </div>
        
        {curriculum.description && (
          <p className="curriculum-description">{curriculum.description}</p>
        )}

        <div className="lessons-grid">
          {curriculum.lessons && Array.isArray(curriculum.lessons) && curriculum.lessons.map((lesson, index) => (
            <div key={lesson.id || index} className="lesson-card">
              <div className="lesson-header">
                <h4>{lesson.title || 'Untitled Lesson'}</h4>
                <span className="lesson-difficulty">{lesson.difficulty || 'Unknown'}</span>
              </div>
              
              <div className="lesson-meta">
                <span className="lesson-duration">⏱️ {lesson.duration || 'N/A'}</span>
                <span className="lesson-type">📝 {lesson.lesson_type || 'Lesson'}</span>
              </div>
              
              <p className="lesson-description">{lesson.description || 'No description available'}</p>
              
              {lesson.objectives && Array.isArray(lesson.objectives) && (
                <div className="lesson-objectives">
                  <strong>Objectives:</strong>
                  <ul>
                    {lesson.objectives.map((obj, i) => (
                      <li key={i}>{obj}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              <button 
                onClick={() => startLesson(lesson.id || lesson.title || `lesson-${index}`)}
                className="start-lesson-button"
              >
                Start Lesson
              </button>
            </div>
          ))}
          
          {/* Show message if no lessons or lessons is not an array */}
          {(!curriculum.lessons || !Array.isArray(curriculum.lessons) || curriculum.lessons.length === 0) && (
            <div className="no-lessons">
              <p>No lessons available for this curriculum. Please try selecting a different subject or check back later.</p>
            </div>
          )}
        </div>
        
        {curriculum.recommendations && Array.isArray(curriculum.recommendations) && (
          <div className="recommendations">
            <h4>📈 Recommended Next Steps</h4>
            <ul>
              {curriculum.recommendations.map((rec, index) => (
                <li key={index}>{rec}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };
  const EmotionBadge = ({ emotion }) => {
    if (!emotion) return null;
    
    // Handle both string and object formats
    let emotionText;
    let confidence;
    
    if (typeof emotion === 'string') {
      emotionText = emotion;
    } else if (typeof emotion === 'object' && emotion.emotion) {
      emotionText = emotion.emotion;
      confidence = emotion.confidence;
    } else {
      return null;
    }
    
    const emotionColors = {
      'confident': 'bg-green-500',
      'curious': 'bg-yellow-500',
      'confused': 'bg-orange-500',
      'frustrated': 'bg-red-500',
      'excited': 'bg-purple-500',
      'anxious': 'bg-gray-500',
      'neutral': 'bg-blue-500'
    };
    
    const emotionIcons = {
      'confident': '😊',
      'curious': '🤔',
      'confused': '😕',
      'frustrated': '😤',
      'excited': '🎉',
      'anxious': '😰',
      'neutral': '😐'
    };

    return (
      <span 
        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-white ${emotionColors[emotionText] || 'bg-gray-500'}`}
        title={confidence ? `Confidence: ${Math.round(confidence * 100)}%` : undefined}
      >
        <span className="mr-1">{emotionIcons[emotionText] || '🎭'}</span>
        {emotionText}
      </span>
    );
  };

  return (
    <div className="app">
      <div className="header">
        <div className="header-content">
          <div className="title-section">
            <h1>🎓 ProfAI</h1>
            <p>Your AI Tutor with Voice Chat</p>
          </div>
          <div className="header-controls">
            <button 
              className="control-button"
              onClick={() => setShowCurriculum(true)}
              title="Browse Curriculum"
            >
              📚 Curriculum
            </button>
            <button 
              className="control-button"
              onClick={() => setShowSettings(!showSettings)}
              title="Settings"
            >
              ⚙️ Settings
            </button>
          </div>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="settings-panel">
          <div className="settings-content">
            <h3>⚙️ Learning Preferences</h3>
            
            <div className="setting-group">
              <label>Learning Path:</label>
              <div className="learning-path-options">
                {Object.entries(LEARNING_PATHS).map(([key, path]) => (
                  <button
                    key={key}
                    className={`path-option ${learningPath === key ? 'active' : ''}`}
                    onClick={() => setLearningPath(key)}
                  >
                    <path.icon size={16} /> {path.name}
                  </button>
                ))}
              </div>
              <p className="path-description">
                {LEARNING_PATHS[learningPath]?.description}
              </p>
            </div>

            <div className="setting-group">
              <label>Delivery Format:</label>
              <select 
                value={deliveryFormat} 
                onChange={(e) => setDeliveryFormat(e.target.value)}
                className="format-select"
              >
                {Object.entries(DELIVERY_FORMATS).map(([key, format]) => (
                  <option key={key} value={key}>
                    {format.name}
                  </option>
                ))}
              </select>
              <p className="format-description">
                {DELIVERY_FORMATS[deliveryFormat]?.description}
              </p>
            </div>

            <div className="setting-group">
              <label>Language:</label>
              <select 
                value={selectedLanguage} 
                onChange={(e) => setSelectedLanguage(e.target.value)}
                className="language-select"
              >
                {Object.entries(LANGUAGES).map(([key, lang]) => (
                  <option key={key} value={key}>
                    {lang.flag} {lang.name}
                  </option>
                ))}
              </select>
              <p className="language-description">
                AI responses and voice will be in {LANGUAGES[selectedLanguage]?.name}
              </p>
            </div>

            <button 
              className="close-settings"
              onClick={() => setShowSettings(false)}
            >
              Close Settings
            </button>
          </div>
        </div>
      )}

      {/* Curriculum Browser Overlay */}
      {showCurriculum && (
        <div className="curriculum-overlay">
          <CurriculumBrowser />
        </div>
      )}

      <div className="chat-container">
        <div className="chat-messages">
          {messages.map((message, index) => (
            <div key={index} className={`message ${message.type}`}>
              <div className="message-content">
                <div className="message-text">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
                <div className="message-meta">
                  <EmotionBadge emotion={message.emotion} />
                  {message.audioUrl && message.audioUrl !== 'loading' && (
                    <div className="audio-player">
                      <audio 
                        controls
                        onLoadedMetadata={(e) => {
                          if (e.target.duration === 0 || isNaN(e.target.duration)) {
                            console.warn('Audio file appears to be empty or corrupted');
                          }
                        }}
                        onError={(e) => {
                          console.warn('Audio playback error:', e);
                        }}
                      >
                        <source src={message.audioUrl} type="audio/mpeg" />
                        Your browser does not support the audio element.
                      </audio>
                      <div className="audio-status">
                        {/* This will be populated by the onLoadedMetadata event if needed */}
                      </div>
                    </div>
                  )}
                  {message.audioUrl === 'loading' && (
                    <div className="audio-loading">
                      🎧 Generating audio...
                    </div>
                  )}
                  {message.type === 'ai' && !message.audioUrl && (
                    <div className="audio-unavailable">
                      🔇 Audio not available
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="loading">
              <div className="loading-spinner"></div>
              <span>Professor is thinking...</span>
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
