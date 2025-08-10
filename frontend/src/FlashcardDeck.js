import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Youtube, BookOpen, RotateCcw, Check, X, Brain } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

const FlashcardDeck = () => {
  const [activeTab, setActiveTab] = useState('create');
  const [flashcardSets, setFlashcardSets] = useState([]);
  const [currentSet, setCurrentSet] = useState(null);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [language, setLanguage] = useState('en');

  // Load flashcard sets on component mount
  useEffect(() => {
    loadFlashcardSets();
  }, []);

  const loadFlashcardSets = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/flashcards/sets`);
      setFlashcardSets(response.data.sets || []);
    } catch (err) {
      console.error('Error loading flashcard sets:', err);
    }
  };

  const loadFullFlashcardSet = async (setId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/flashcards/sets/${setId}`);
      return response.data;
    } catch (err) {
      console.error('Error loading flashcard set:', err);
      return null;
    }
  };

  const processYouTubeVideo = async () => {
    if (!youtubeUrl.trim()) {
      setError('Please enter a YouTube URL');
      return;
    }

    setIsProcessing(true);
    setError('');

    try {
      const response = await axios.post(`${API_BASE_URL}/youtube/process`, {
        url: youtubeUrl.trim(),
        language: language
      });

      if (response.data.success) {
        setYoutubeUrl('');
        await loadFlashcardSets();
        setActiveTab('study');
        setCurrentSet(response.data.flashcard_set);
        setCurrentCardIndex(0);
        setShowAnswer(false);
      } else {
        setError(response.data.error || 'Failed to process video');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Error processing YouTube video');
    } finally {
      setIsProcessing(false);
    }
  };

  const updateCardStatus = async (cardId, status) => {
    if (!currentSet) return;

    try {
      await axios.put(`${API_BASE_URL}/flashcards/sets/${currentSet.id}/cards/${cardId}`, {
        card_id: cardId,
        status: status
      });

      // Update local state
      const updatedCards = currentSet.cards.map(card =>
        card.id === cardId 
          ? { ...card, status, review_count: card.review_count + 1 }
          : card
      );

      const updatedSet = {
        ...currentSet,
        cards: updatedCards,
        learned_cards: updatedCards.filter(c => c.status === 'learned').length,
        learning_cards: updatedCards.filter(c => c.status === 'learning').length
      };

      setCurrentSet(updatedSet);
      
      // Update the sets list
      setFlashcardSets(prev => prev.map(set => 
        set.id === currentSet.id 
          ? { ...set, learned_cards: updatedSet.learned_cards, learning_cards: updatedSet.learning_cards }
          : set
      ));

    } catch (err) {
      console.error('Error updating card status:', err);
    }
  };

  const nextCard = () => {
    if (currentSet && currentSet.cards && currentCardIndex < currentSet.cards.length - 1) {
      setCurrentCardIndex(currentCardIndex + 1);
      setShowAnswer(false);
    }
  };

  const prevCard = () => {
    if (currentCardIndex > 0) {
      setCurrentCardIndex(currentCardIndex - 1);
      setShowAnswer(false);
    }
  };

  const resetDeck = () => {
    setCurrentCardIndex(0);
    setShowAnswer(false);
  };

  const getProgressPercentage = (set) => {
    if (!set || set.total_cards === 0) return 0;
    return Math.round((set.learned_cards / set.total_cards) * 100);
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case 'easy': return '#10b981';
      case 'medium': return '#f59e0b';
      case 'hard': return '#ef4444';
      default: return '#6b7280';
    }
  };

  return (
    <div className="flashcard-deck">
      {/* Tab Navigation */}
      <div className="flashcard-tabs">
        <button 
          className={`tab ${activeTab === 'create' ? 'active' : ''}`}
          onClick={() => setActiveTab('create')}
        >
          <Youtube size={20} />
          Create from YouTube
        </button>
        <button 
          className={`tab ${activeTab === 'study' ? 'active' : ''}`}
          onClick={() => setActiveTab('study')}
        >
          <Brain size={20} />
          Study Flashcards
        </button>
        <button 
          className={`tab ${activeTab === 'library' ? 'active' : ''}`}
          onClick={() => setActiveTab('library')}
        >
          <BookOpen size={20} />
          My Library
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-message">
          <X size={16} />
          {error}
          <button onClick={() => setError('')}>×</button>
        </div>
      )}

      {/* Create Tab */}
      {activeTab === 'create' && (
        <div className="create-tab">
          <div className="create-header">
            <h2>📺 Create Flashcards from YouTube</h2>
            <p>Enter a YouTube URL for educational content and I'll create study flashcards for you!</p>
          </div>
          
          <div className="url-input-section">
            <div className="input-group">
              <input
                type="url"
                placeholder="https://www.youtube.com/watch?v=..."
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                className="youtube-input"
                disabled={isProcessing}
              />
              <select 
                value={language} 
                onChange={(e) => setLanguage(e.target.value)}
                className="language-select"
                disabled={isProcessing}
              >
                <option value="en">English</option>
                <option value="es">Español</option>
                <option value="fr">Français</option>
                <option value="de">Deutsch</option>
                <option value="it">Italiano</option>
                <option value="pt">Português</option>
              </select>
            </div>
            
            <button 
              onClick={processYouTubeVideo}
              disabled={isProcessing || !youtubeUrl.trim()}
              className="process-button"
            >
              {isProcessing ? (
                <>
                  <div className="spinner"></div>
                  Processing Video...
                </>
              ) : (
                <>
                  <Youtube size={20} />
                  Generate Flashcards
                </>
              )}
            </button>
          </div>

          <div className="info-section">
            <div className="info-card">
              <h3>✨ How it works</h3>
              <ol>
                <li>Paste a YouTube URL for educational content</li>
                <li>AI analyzes if the content is suitable for learning</li>
                <li>Creates comprehensive flashcards from key concepts</li>
                <li>Study with spaced repetition like Anki</li>
              </ol>
            </div>
            
            <div className="info-card">
              <h3>📚 Best Results With</h3>
              <ul>
                <li>Educational tutorials and lectures</li>
                <li>Course content and lessons</li>
                <li>How-to guides and explanations</li>
                <li>Academic or professional training</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Study Tab */}
      {activeTab === 'study' && (
        <div className="study-tab">
          {currentSet ? (
            <div className="flashcard-container">
              <div className="study-header">
                <h2>{currentSet.title}</h2>
                <div className="study-meta">
                  <span className="card-counter">
                    Card {currentCardIndex + 1} of {currentSet.cards ? currentSet.cards.length : 0}
                  </span>
                  <div className="progress-bar">
                    <div 
                      className="progress-fill" 
                      style={{ width: `${getProgressPercentage(currentSet)}%` }}
                    ></div>
                  </div>
                  <span className="progress-text">
                    {getProgressPercentage(currentSet)}% Complete
                  </span>
                </div>
              </div>

              {currentSet && currentSet.cards && currentSet.cards.length > 0 && (
                <div className="flashcard">
                  <div className="card-content">
                    <div className="card-header">
                      <span 
                        className="difficulty-badge"
                        style={{ backgroundColor: getDifficultyColor(currentSet.cards[currentCardIndex].difficulty) }}
                      >
                        {currentSet.cards[currentCardIndex].difficulty}
                      </span>
                      <span className="category-badge">
                        {currentSet.cards[currentCardIndex].category}
                      </span>
                    </div>

                    <div className="card-question">
                      <h3>Question:</h3>
                      <p>{currentSet.cards[currentCardIndex].question}</p>
                    </div>

                    {showAnswer && (
                      <div className="card-answer">
                        <h3>Answer:</h3>
                        <p>{currentSet.cards[currentCardIndex].answer}</p>
                        <div className="tags">
                          {currentSet.cards[currentCardIndex].tags.map((tag, index) => (
                            <span key={index} className="tag">#{tag}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="card-actions">
                    {!showAnswer ? (
                      <button 
                        className="reveal-button"
                        onClick={() => setShowAnswer(true)}
                      >
                        Show Answer
                      </button>
                    ) : (
                      <div className="answer-actions">
                        <button 
                          className="action-button incorrect"
                          onClick={() => {
                            updateCardStatus(currentSet.cards[currentCardIndex].id, 'review');
                            nextCard();
                          }}
                        >
                          <X size={16} />
                          Need Review
                        </button>
                        <button 
                          className="action-button learning"
                          onClick={() => {
                            updateCardStatus(currentSet.cards[currentCardIndex].id, 'learning');
                            nextCard();
                          }}
                        >
                          <RotateCcw size={16} />
                          Still Learning
                        </button>
                        <button 
                          className="action-button correct"
                          onClick={() => {
                            updateCardStatus(currentSet.cards[currentCardIndex].id, 'learned');
                            nextCard();
                          }}
                        >
                          <Check size={16} />
                          Got It!
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div className="navigation-controls">
                <button 
                  onClick={prevCard}
                  disabled={currentCardIndex === 0}
                  className="nav-button"
                >
                  ← Previous
                </button>
                <button 
                  onClick={resetDeck}
                  className="nav-button reset"
                >
                  <RotateCcw size={16} />
                  Reset Deck
                </button>
                <button 
                  onClick={nextCard}
                  disabled={currentCardIndex === (currentSet.cards ? currentSet.cards.length - 1 : 0)}
                  className="nav-button"
                >
                  Next →
                </button>
              </div>
            </div>
          ) : (
            <div className="no-set-selected">
              <Brain size={64} />
              <h2>No flashcard set selected</h2>
              <p>Create flashcards from a YouTube video or select a set from your library</p>
              <button 
                onClick={() => setActiveTab('create')}
                className="primary-button"
              >
                <Youtube size={20} />
                Create Flashcards
              </button>
            </div>
          )}
        </div>
      )}

      {/* Library Tab */}
      {activeTab === 'library' && (
        <div className="library-tab">
          <div className="library-header">
            <h2>📚 My Flashcard Library</h2>
            <p>Manage your flashcard collections</p>
          </div>

          {flashcardSets && flashcardSets.length > 0 ? (
            <div className="flashcard-grid">
              {flashcardSets.map((set) => (
                <div key={set.id} className="flashcard-set-card">
                  <div className="set-header">
                    <h3>{set.title}</h3>
                    <div className="set-meta">
                      <span className="video-title">{set.video_title}</span>
                      <span className="card-count">{set.total_cards || 0} cards</span>
                    </div>
                  </div>

                  <div className="set-progress">
                    <div className="progress-stats">
                      <div className="stat">
                        <span className="stat-number" style={{ color: '#10b981' }}>
                          {set.learned_cards || 0}
                        </span>
                        <span className="stat-label">Learned</span>
                      </div>
                      <div className="stat">
                        <span className="stat-number" style={{ color: '#f59e0b' }}>
                          {set.learning_cards || 0}
                        </span>
                        <span className="stat-label">Learning</span>
                      </div>
                      <div className="stat">
                        <span className="stat-number" style={{ color: '#6b7280' }}>
                          {(set.total_cards || 0) - (set.learned_cards || 0) - (set.learning_cards || 0)}
                        </span>
                        <span className="stat-label">New</span>
                      </div>
                    </div>
                    
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{ width: `${getProgressPercentage(set)}%` }}
                      ></div>
                    </div>
                    <span className="progress-percentage">
                      {getProgressPercentage(set)}% Complete
                    </span>
                  </div>

                  <div className="set-actions">
                    <button 
                      className="study-button"
                      onClick={async () => {
                        const fullSet = await loadFullFlashcardSet(set.id);
                        if (fullSet) {
                          setCurrentSet(fullSet);
                          setCurrentCardIndex(0);
                          setShowAnswer(false);
                          setActiveTab('study');
                        }
                      }}
                    >
                      <Brain size={16} />
                      Study
                    </button>
                    <button 
                      className="delete-button"
                      onClick={async () => {
                        if (window.confirm('Delete this flashcard set?')) {
                          try {
                            await axios.delete(`${API_BASE_URL}/flashcards/sets/${set.id}`);
                            await loadFlashcardSets();
                          } catch (err) {
                            console.error('Error deleting set:', err);
                          }
                        }
                      }}
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-library">
              <BookOpen size={64} />
              <h2>No flashcard sets yet</h2>
              <p>Create your first flashcard set from a YouTube video</p>
              <button 
                onClick={() => setActiveTab('create')}
                className="primary-button"
              >
                <Youtube size={20} />
                Create from YouTube
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FlashcardDeck;
