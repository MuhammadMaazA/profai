import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { 
  BookOpen, Clock, Trophy, PlayCircle, CheckCircle, Target, Users, Plus, Upload, Trash2, Eye,
  Youtube, Brain, Play, Check, ArrowLeft
} from 'lucide-react';
import PersonalizedQuiz from './PersonalizedQuiz';
import ConfusionDetector from './ConfusionDetector';
import SmartReadingAssistant from './SmartReadingAssistant';

const API_BASE_URL = 'http://localhost:8000';

const PlaylistCurriculumManager = () => {
  const [curricula, setCurricula] = useState([]);
  const [selectedCurriculum, setSelectedCurriculum] = useState(null);
  const [selectedChapter, setSelectedChapter] = useState(null);
  const [activeView, setActiveView] = useState('overview'); // overview, curriculum, chapter, quiz
  const [newPlaylistUrl, setNewPlaylistUrl] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  
  // New state for advanced features
  const [showQuiz, setShowQuiz] = useState(false);
  const [confusionDetectionActive, setConfusionDetectionActive] = useState(true);
  const [useSmartReading, setUseSmartReading] = useState(true);
  const [confusionAlert, setConfusionAlert] = useState(null);
  
  // Ref for chapter content to track reading position
  const chapterContentRef = useRef(null);

  useEffect(() => {
    loadCurricula();
  }, []);

  const loadCurricula = async () => {
    console.log('Loading curricula from:', `${API_BASE_URL}/playlist/curricula`);
    try {
      const response = await axios.get(`${API_BASE_URL}/playlist/curricula`);
      console.log('Curricula response:', response.data);
      setCurricula(response.data.curricula);
      console.log('Set curricula state:', response.data.curricula);
    } catch (err) {
      console.error('Error loading curricula:', err);
      console.error('Error details:', err.response?.data);
    }
  };

  const processPlaylist = async () => {
    if (!newPlaylistUrl.trim()) return;

    setIsProcessing(true);
    setProcessingStatus('Processing playlist...');
    
    try {
      const response = await axios.post(`${API_BASE_URL}/playlist/process`, {
        playlist_url: newPlaylistUrl
      });

      if (response.data.success) {
        setProcessingStatus('Curriculum created successfully!');
        setTimeout(() => {
          setIsProcessing(false);
          setProcessingStatus('');
          setNewPlaylistUrl('');
          setShowAddForm(false);
          loadCurricula();
        }, 2000);
      } else {
        setProcessingStatus(`Error: ${response.data.error}`);
        setTimeout(() => {
          setIsProcessing(false);
          setProcessingStatus('');
        }, 3000);
      }
    } catch (err) {
      setProcessingStatus(`Error: ${err.response?.data?.detail || err.message}`);
      setTimeout(() => {
        setIsProcessing(false);
        setProcessingStatus('');
      }, 3000);
    }
  };

  const loadCurriculumDetails = async (curriculumId) => {
    console.log('loadCurriculumDetails called with ID:', curriculumId);
    try {
      console.log('Making API request to:', `${API_BASE_URL}/playlist/curriculum/${curriculumId}`);
      const response = await axios.get(`${API_BASE_URL}/playlist/curriculum/${curriculumId}`);
      console.log('API response:', response.data);
      setSelectedCurriculum(response.data);
      setActiveView('curriculum');
      console.log('Updated state - activeView set to: curriculum');
    } catch (err) {
      console.error('Error loading curriculum details:', err);
      console.error('Error details:', err.response?.data);
    }
  };

  const loadChapterDetails = async (curriculumId, chapterId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/playlist/curriculum/${curriculumId}/chapter/${chapterId}`);
      setSelectedChapter(response.data);
      setActiveView('chapter');
    } catch (err) {
      console.error('Error loading chapter details:', err);
    }
  };

  const updateChapterProgress = async (curriculumId, chapterId, completed) => {
    try {
      await axios.post(`${API_BASE_URL}/playlist/curriculum/${curriculumId}/chapter/${chapterId}/progress`, {
        curriculum_id: curriculumId,
        chapter_id: chapterId,
        completed: completed
      });
      
      // If chapter is marked as complete, trigger quiz
      if (completed && selectedChapter) {
        setShowQuiz(true);
        setActiveView('quiz');
      }
      
      // Reload curriculum to update progress
      loadCurriculumDetails(curriculumId);
    } catch (err) {
      console.error('Error updating chapter progress:', err);
    }
  };

  // Handler for confusion detection
  const handleConfusionDetected = (confusionData) => {
    console.log('Confusion detected:', confusionData);
    
    // Only show alert if confusion is detected AND we have a contextual explanation
    if (confusionData.confusion_detected && confusionData.contextual_explanation) {
      setConfusionAlert({
        type: 'confusion',
        level: confusionData.confusion_level,
        explanation: confusionData.contextual_explanation,
        confusedText: confusionData.confused_text || confusionData.contextText,
        suggestions: confusionData.suggestions || []
      });
      
      // Auto-dismiss after 20 seconds
      setTimeout(() => {
        setConfusionAlert(null);
      }, 20000);
    }
  };

  // Handler for quiz completion
  const handleQuizComplete = (quizResults) => {
    console.log('Quiz completed:', quizResults);
    setShowQuiz(false);
    setActiveView('chapter');
    
    // Show success message or recommendations based on results
    if (quizResults.score >= 0.8) {
      alert(`Excellent work! You scored ${Math.round(quizResults.percentage)}%`);
    } else if (quizResults.score >= 0.6) {
      alert(`Good job! You scored ${Math.round(quizResults.percentage)}%. Review the concepts marked as weak.`);
    } else {
      alert(`You scored ${Math.round(quizResults.percentage)}%. Consider reviewing this chapter before moving on.`);
    }
  };

  const deleteCurriculum = async (curriculumId) => {
    if (!window.confirm('Are you sure you want to delete this curriculum?')) return;
    
    try {
      await axios.delete(`${API_BASE_URL}/playlist/curriculum/${curriculumId}`);
      loadCurricula();
    } catch (err) {
      console.error('Error deleting curriculum:', err);
    }
  };

  const getProgressColor = (percentage) => {
    if (percentage === 100) return '#10b981';
    if (percentage >= 75) return '#3b82f6';
    if (percentage >= 50) return '#f59e0b';
    if (percentage >= 25) return '#ef4444';
    return '#6b7280';
  };

  // Chapter Detail View
  if (activeView === 'chapter' && selectedChapter) {
    return (
      <div className="playlist-curriculum-manager">
        {/* Confusion Alert */}
        {confusionAlert && (
          <div className="confusion-alert">
            <div className="confusion-content">
              <div className="confusion-header">
                <h3>🤔 I noticed you might be confused...</h3>
                <span className="confusion-level">
                  Confusion Level: {Math.round(confusionAlert.level * 100)}%
                </span>
                <button 
                  className="dismiss-btn"
                  onClick={() => setConfusionAlert(null)}
                >
                  ×
                </button>
              </div>
              
              {confusionAlert.confusedText && (
                <div className="confused-text">
                  <strong>You were reading:</strong>
                  <p>"{confusionAlert.confusedText.slice(0, 200)}..."</p>
                </div>
              )}
              
              <div className="explanation">
                <strong>Let me explain this part:</strong>
                <ReactMarkdown>{confusionAlert.explanation}</ReactMarkdown>
              </div>
              
              {confusionAlert.suggestions && confusionAlert.suggestions.length > 0 && (
                <div className="suggestions">
                  <strong>Suggestions:</strong>
                  <ul>
                    {confusionAlert.suggestions.map((suggestion, index) => (
                      <li key={index}>{suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* Confusion Detection */}
        <ConfusionDetector 
          currentText={selectedChapter.notes || selectedChapter.description || ''}
          onConfusionDetected={handleConfusionDetected}
          isActive={confusionDetectionActive}
          contentRef={chapterContentRef}
        />
        
        <div className="chapter-viewer">
          <div className="chapter-header">
            <button 
              className="back-button"
              onClick={() => setActiveView('curriculum')}
            >
              <ArrowLeft size={16} />
              Back to Curriculum
            </button>
            
            <div className="chapter-meta">
              <h1>{selectedChapter.title}</h1>
              <div className="chapter-info">
                <span className="duration">
                  <Clock size={16} />
                  {selectedChapter.duration}
                </span>
                <a 
                  href={selectedChapter.video_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="video-link"
                >
                  <Youtube size={16} />
                  Watch Video
                </a>
              </div>
            </div>
          </div>

          <div className="chapter-content" ref={chapterContentRef}>
            {selectedChapter.description && (
              <div className="chapter-section">
                <h2>Description</h2>
                <div className="content-block">
                  <p>{selectedChapter.description}</p>
                </div>
              </div>
            )}

            {selectedChapter.notes && (
              <div className="chapter-section">
                <h2>📝 Study Notes</h2>
                {useSmartReading ? (
                  <SmartReadingAssistant 
                    content={selectedChapter.notes}
                    title={selectedChapter.title}
                  />
                ) : (
                  <div className="content-block notes-content">
                    <ReactMarkdown>{selectedChapter.notes}</ReactMarkdown>
                  </div>
                )}
              </div>
            )}

            {selectedChapter.flashcards && selectedChapter.flashcards.length > 0 && (
              <div className="chapter-section">
                <h2>🧠 Flashcards ({selectedChapter.flashcards.length})</h2>
                <div className="flashcards-grid">
                  {selectedChapter.flashcards.map((card, index) => (
                    <div key={card.id} className="flashcard-preview">
                      <div className="flashcard-header">
                        <span className="flashcard-number">#{index + 1}</span>
                        <span className={`difficulty-badge difficulty-${card.difficulty}`}>
                          {card.difficulty}
                        </span>
                      </div>
                      <div className="flashcard-content">
                        <div className="question">
                          <strong>Q:</strong> {card.question}
                        </div>
                        <div className="answer">
                          <strong>A:</strong> {card.answer}
                        </div>
                      </div>
                      {card.tags && card.tags.length > 0 && (
                        <div className="flashcard-tags">
                          {card.tags.map((tag, i) => (
                            <span key={i} className="tag">#{tag}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="chapter-actions">
            {/* Feature Toggles */}
            <div className="feature-controls">
              <button 
                className={`feature-toggle ${confusionDetectionActive ? 'active' : ''}`}
                onClick={() => setConfusionDetectionActive(!confusionDetectionActive)}
                title="Toggle confusion detection"
              >
                <Brain size={16} />
                {confusionDetectionActive ? 'Confusion Detection ON' : 'Confusion Detection OFF'}
              </button>
              
              <button 
                className={`feature-toggle ${useSmartReading ? 'active' : ''}`}
                onClick={() => setUseSmartReading(!useSmartReading)}
                title="Toggle smart reading assistant"
              >
                <BookOpen size={16} />
                {useSmartReading ? 'Smart Reading ON' : 'Smart Reading OFF'}
              </button>

              <button 
                className="quiz-trigger-btn"
                onClick={() => {
                  setShowQuiz(true);
                  setActiveView('quiz');
                }}
                title="Take quiz for this chapter"
              >
                <Trophy size={16} />
                Take Quiz
              </button>
            </div>

            <button 
              className={`complete-chapter-btn ${selectedChapter.completed ? 'completed' : ''}`}
              onClick={() => updateChapterProgress(
                selectedCurriculum?.id, 
                selectedChapter.id, 
                !selectedChapter.completed
              )}
            >
              {selectedChapter.completed ? <Check size={16} /> : <CheckCircle size={16} />}
              {selectedChapter.completed ? 'Completed' : 'Mark as Complete'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Quiz View
  if (activeView === 'quiz' && selectedChapter) {
    return (
      <div className="playlist-curriculum-manager">
        <div className="quiz-section">
          <div className="quiz-header">
            <button 
              className="back-button"
              onClick={() => {
                setShowQuiz(false);
                setActiveView('chapter');
              }}
            >
              <ArrowLeft size={16} />
              Back to Chapter
            </button>
            <h2>🎯 Chapter Quiz: {selectedChapter.title}</h2>
          </div>
          
          <PersonalizedQuiz 
            chapterContent={selectedChapter.notes || selectedChapter.description || ''}
            chapterTitle={selectedChapter.title}
            onQuizComplete={handleQuizComplete}
          />
        </div>
      </div>
    );
  }

  // Curriculum Detail View
  if (activeView === 'curriculum' && selectedCurriculum) {
    return (
      <div className="playlist-curriculum-manager">
        <div className="curriculum-detail">
          <div className="curriculum-header">
            <button 
              className="back-button"
              onClick={() => {
                setActiveView('overview');
                setSelectedCurriculum(null);
              }}
            >
              <ArrowLeft size={16} />
              Back to Curricula
            </button>
            
            <div className="curriculum-info">
              <h1>{selectedCurriculum.title}</h1>
              <p>{selectedCurriculum.description}</p>
              
              <div className="curriculum-meta">
                <span className="creator">
                  <Users size={16} />
                  {selectedCurriculum.creator}
                </span>
                <span className="progress">
                  <Trophy size={16} />
                  {selectedCurriculum.completed_chapters}/{selectedCurriculum.total_chapters} chapters completed
                </span>
                <span className="progress-percentage">
                  <Target size={16} />
                  {Math.round(selectedCurriculum.progress_percentage)}% progress
                </span>
              </div>

              <div className="progress-bar-container">
                <div className="progress-bar">
                  <div 
                    className="progress-fill"
                    style={{ 
                      width: `${selectedCurriculum.progress_percentage}%`,
                      backgroundColor: getProgressColor(selectedCurriculum.progress_percentage)
                    }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <div className="chapters-list">
            <h2>📚 Chapters</h2>
            {selectedCurriculum.chapters.map((chapter, index) => (
              <div key={chapter.id} className={`chapter-card ${chapter.completed ? 'completed' : ''}`}>
                <div className="chapter-number">
                  {chapter.completed ? <CheckCircle size={20} /> : index + 1}
                </div>
                <div className="chapter-info">
                  <h3>{chapter.title}</h3>
                  <div className="chapter-meta">
                    <span className="duration">
                      <Clock size={14} />
                      {chapter.duration}
                    </span>
                    {chapter.flashcards && chapter.flashcards.length > 0 && (
                      <span className="flashcard-count">
                        <Brain size={14} />
                        {chapter.flashcards.length} flashcards
                      </span>
                    )}
                  </div>
                </div>
                <div className="chapter-actions">
                  <button 
                    className="view-chapter-btn"
                    onClick={() => loadChapterDetails(selectedCurriculum.id, chapter.id)}
                  >
                    <Eye size={16} />
                    Study
                  </button>
                  <a 
                    href={chapter.video_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="watch-video-btn"
                  >
                    <Play size={16} />
                    Watch
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Overview - List of Curricula
  return (
    <div className="playlist-curriculum-manager">
      <div className="curriculum-overview">
        <div className="overview-header">
          <h1>🎓 YouTube Playlist Curricula</h1>
          <p>Create structured learning curricula from YouTube playlists</p>
          
          <button 
            className="add-curriculum-btn"
            onClick={() => setShowAddForm(!showAddForm)}
          >
            <Plus size={16} />
            Add New Curriculum
          </button>
        </div>

        {showAddForm && (
          <div className="add-curriculum-form">
            <div className="form-content">
              <h3>Create Curriculum from YouTube Playlist</h3>
              <p>Enter a YouTube playlist URL to automatically generate a structured curriculum with notes and flashcards for each video.</p>
              
              <div className="input-group">
                <input
                  type="url"
                  placeholder="https://www.youtube.com/playlist?list=..."
                  value={newPlaylistUrl}
                  onChange={(e) => setNewPlaylistUrl(e.target.value)}
                  disabled={isProcessing}
                />
                <button 
                  onClick={processPlaylist}
                  disabled={isProcessing || !newPlaylistUrl.trim()}
                  className="process-btn"
                >
                  {isProcessing ? <Upload className="spinning" size={16} /> : <Upload size={16} />}
                  {isProcessing ? 'Processing...' : 'Create Curriculum'}
                </button>
              </div>
              
              {processingStatus && (
                <div className={`processing-status ${isProcessing ? 'processing' : 'completed'}`}>
                  {processingStatus}
                </div>
              )}
            </div>
          </div>
        )}

        {curricula.length === 0 ? (
          <div className="empty-state">
            <Youtube size={64} />
            <h3>No Curricula Yet</h3>
            <p>Create your first curriculum by adding a YouTube playlist above.</p>
          </div>
        ) : (
          <div className="curricula-grid">
            {curricula.map((curriculum) => (
              <div key={curriculum.id} className="curriculum-card">
                <div className="curriculum-icon">
                  <Youtube size={32} />
                </div>
                
                <div className="curriculum-content">
                  <h3>{curriculum.title}</h3>
                  <p className="curriculum-description">{curriculum.description}</p>
                  
                  <div className="curriculum-stats">
                    <div className="stat">
                      <BookOpen size={16} />
                      <span>{curriculum.total_chapters} chapters</span>
                    </div>
                    <div className="stat">
                      <Users size={16} />
                      <span>{curriculum.creator}</span>
                    </div>
                    <div className="stat">
                      <Trophy size={16} />
                      <span>{Math.round(curriculum.progress_percentage)}% complete</span>
                    </div>
                  </div>

                  <div className="progress-bar-container">
                    <div className="progress-bar">
                      <div 
                        className="progress-fill"
                        style={{ 
                          width: `${curriculum.progress_percentage}%`,
                          backgroundColor: getProgressColor(curriculum.progress_percentage)
                        }}
                      ></div>
                    </div>
                    <span className="progress-text">
                      {curriculum.completed_chapters}/{curriculum.total_chapters} chapters
                    </span>
                  </div>
                </div>
                
                <div className="curriculum-actions">
                  <button 
                    className="continue-btn"
                    onClick={() => {
                      console.log('Start Learning clicked for curriculum:', curriculum.id);
                      console.log('Full curriculum object:', curriculum);
                      loadCurriculumDetails(curriculum.id);
                    }}
                  >
                    <PlayCircle size={16} />
                    {curriculum.progress_percentage > 0 ? 'Continue' : 'Start Learning'}
                  </button>
                  <button 
                    className="delete-btn"
                    onClick={() => deleteCurriculum(curriculum.id)}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PlaylistCurriculumManager;

