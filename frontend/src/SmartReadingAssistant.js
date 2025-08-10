import React, { useState, useRef, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const SmartReadingAssistant = ({ content, title }) => {
  const [contextualHelp, setContextualHelp] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedText, setSelectedText] = useState('');
  const [showHelpPanel, setShowHelpPanel] = useState(false);
  const [readingProgress, setReadingProgress] = useState(0);
  const [currentSection, setCurrentSection] = useState('');
  
  const contentRef = useRef(null);
  const debounceRef = useRef(null);

  // Define analyzeCurrentReading first
  const analyzeCurrentReading = useCallback(async (visibleText, scrollPosition) => {
    if (!visibleText || isAnalyzing) return;

    setIsAnalyzing(true);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/track-reading`, {
        text_content: content,
        user_position: {
          scroll_position: scrollPosition / 100,
          visible_text: visibleText
        }
      });

      setContextualHelp(response.data);
      
      // Auto-show help panel if text is difficult
      if (response.data.difficulty_estimate === 'hard') {
        setShowHelpPanel(true);
      }

    } catch (error) {
      console.error('Error analyzing reading:', error);
    } finally {
      setIsAnalyzing(false);
    }
  }, [content, isAnalyzing]);

  // Track reading progress and visible content
  const handleScroll = useCallback(() => {
    if (!contentRef.current) return;

    const element = contentRef.current;
    const scrollTop = element.scrollTop;
    const scrollHeight = element.scrollHeight - element.clientHeight;
    const progress = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0;
    
    setReadingProgress(progress);

    // Get visible text for contextual analysis
    const visibleText = getVisibleText();
    if (visibleText && visibleText !== currentSection) {
      setCurrentSection(visibleText);
      
      // Debounce the analysis call
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
      
      debounceRef.current = setTimeout(() => {
        analyzeCurrentReading(visibleText, progress);
      }, 1000);
    }
  }, [currentSection, analyzeCurrentReading]);

  useEffect(() => {
    const element = contentRef.current;
    if (element) {
      element.addEventListener('scroll', handleScroll);
      return () => element.removeEventListener('scroll', handleScroll);
    }
  }, [handleScroll]);

  const getVisibleText = () => {
    if (!contentRef.current) return '';

    const element = contentRef.current;
    const rect = element.getBoundingClientRect();
    const centerY = rect.top + rect.height / 2;

    // Find the paragraph that's currently in the center of the view
    const paragraphs = element.querySelectorAll('p, h1, h2, h3, h4, h5, h6');
    
    for (let p of paragraphs) {
      const pRect = p.getBoundingClientRect();
      if (pRect.top <= centerY && pRect.bottom >= centerY) {
        return p.textContent.slice(0, 300); // Limit to 300 chars
      }
    }

    return '';
  };

  // Handle text selection for instant help
  const handleTextSelection = () => {
    const selection = window.getSelection();
    const text = selection.toString().trim();
    
    if (text && text.length > 10) {
      setSelectedText(text);
      generateInstantHelp(text);
    }
  };

  const generateInstantHelp = async (text) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/track-reading`, {
        text_content: content,
        user_position: {
          scroll_position: readingProgress / 100,
          visible_text: text
        }
      });

      setContextualHelp({
        ...response.data,
        selected_text: text,
        is_selection: true
      });
      setShowHelpPanel(true);

    } catch (error) {
      console.error('Error generating instant help:', error);
    }
  };

  const toggleHelpPanel = () => {
    setShowHelpPanel(!showHelpPanel);
  };

  const dismissHelp = () => {
    setShowHelpPanel(false);
    setSelectedText('');
  };

  return (
    <div className="smart-reading-container">
      {/* Reading Progress Bar */}
      <div className="reading-progress-bar">
        <div 
          className="progress-fill" 
          style={{ width: `${readingProgress}%` }}
        />
        <span className="progress-text">
          {Math.round(readingProgress)}% complete
        </span>
      </div>

      {/* Main Content Area */}
      <div className="reading-content-wrapper">
        {/* Content Panel */}
        <div 
          ref={contentRef}
          className="reading-content"
          onMouseUp={handleTextSelection}
        >
          <h1>{title}</h1>
          <ReactMarkdown>{content}</ReactMarkdown>
          
          {/* Current Section Indicator */}
          {currentSection && (
            <div className="current-section-indicator">
              <div className="section-highlight">
                📍 Current Focus
              </div>
            </div>
          )}
        </div>

        {/* Contextual Help Panel */}
        <div className={`help-panel ${showHelpPanel ? 'visible' : 'hidden'}`}>
          <div className="help-header">
            <h4>💡 Reading Assistant</h4>
            <div className="help-controls">
              <button 
                onClick={toggleHelpPanel}
                className="toggle-help-btn"
                title={showHelpPanel ? 'Hide Help' : 'Show Help'}
              >
                {showHelpPanel ? '👁️‍🗨️' : '💡'}
              </button>
              {showHelpPanel && (
                <button onClick={dismissHelp} className="close-help-btn">×</button>
              )}
            </div>
          </div>

          {showHelpPanel && contextualHelp && (
            <div className="help-content">
              {contextualHelp.is_selection && (
                <div className="selected-text-help">
                  <h5>📝 Selected Text Help</h5>
                  <blockquote>"{selectedText}"</blockquote>
                </div>
              )}

              <div className="contextual-explanation">
                <h5>🎯 Simple Explanation</h5>
                <div className="explanation-text">
                  <ReactMarkdown>{contextualHelp.contextual_help}</ReactMarkdown>
                </div>
              </div>

              {contextualHelp.key_concepts && contextualHelp.key_concepts.length > 0 && (
                <div className="key-concepts">
                  <h5>🔑 Key Concepts</h5>
                  <div className="concept-tags">
                    {contextualHelp.key_concepts.map((concept, index) => (
                      <span key={index} className="concept-tag">{concept}</span>
                    ))}
                  </div>
                </div>
              )}

              <div className="reading-stats">
                <div className="stat-item">
                  <span className="stat-label">Difficulty</span>
                  <span className={`difficulty-badge ${contextualHelp.difficulty_estimate}`}>
                    {contextualHelp.difficulty_estimate}
                  </span>
                </div>
                
                {contextualHelp.reading_time_estimate && (
                  <div className="stat-item">
                    <span className="stat-label">Est. Time</span>
                    <span className="time-estimate">
                      {Math.round(contextualHelp.reading_time_estimate / 60)}m
                    </span>
                  </div>
                )}
              </div>

              <div className="reading-tips">
                <h5>💭 Reading Tips</h5>
                <ul>
                  <li>Highlight text you don't understand for instant help</li>
                  <li>Take breaks every 20 minutes for better retention</li>
                  <li>Summarize each section in your own words</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Analysis Status */}
      {isAnalyzing && (
        <div className="analysis-status">
          <div className="analyzing-indicator">
            <span className="spinner">🔍</span>
            Analyzing reading context...
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="reading-instructions">
        <p>💡 <strong>Pro tip:</strong> Select any text that confuses you for instant explanations!</p>
      </div>
    </div>
  );
};

export default SmartReadingAssistant;
