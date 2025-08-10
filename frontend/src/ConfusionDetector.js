import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const ConfusionDetector = ({ currentText, onConfusionDetected, isActive = true, contentRef = null }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [confusionData, setConfusionData] = useState(null);
  const [cameraPermission, setCameraPermission] = useState(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [currentReadingPosition, setCurrentReadingPosition] = useState(null);
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (isActive) {
      initializeCamera();
      startPositionTracking();
    } else {
      stopCamera();
      stopPositionTracking();
    }

    return () => {
      stopCamera();
      stopPositionTracking();
    };
  }, [isActive, initializeCamera, startPositionTracking]);

  const startPositionTracking = () => {
    // Track scroll position to determine what user is reading
    const handleScroll = () => {
      if (contentRef && contentRef.current) {
        const position = getCurrentReadingPosition();
        setCurrentReadingPosition(position);
      }
    };

    window.addEventListener('scroll', handleScroll);
    // Store the cleanup function
    window.scrollCleanup = () => window.removeEventListener('scroll', handleScroll);
  };

  const stopPositionTracking = () => {
    if (window.scrollCleanup) {
      window.scrollCleanup();
      delete window.scrollCleanup;
    }
  };

  const getCurrentReadingPosition = () => {
    if (!contentRef || !contentRef.current) return null;

    const contentElement = contentRef.current;
    const viewportHeight = window.innerHeight;
    const scrollTop = window.scrollY;
    
    // Find the element that's currently in the center of the viewport
    const centerY = scrollTop + viewportHeight / 2;
    
    // Get all text nodes and find which one is at the center
    const walker = document.createTreeWalker(
      contentElement,
      NodeFilter.SHOW_TEXT,
      null,
      false
    );

    let currentNode;
    let bestNode = null;
    let bestDistance = Infinity;

    while ((currentNode = walker.nextNode())) {
      const range = document.createRange();
      range.selectNodeContents(currentNode);
      const rect = range.getBoundingClientRect();
      
      if (rect.height > 0) {
        const nodeCenter = rect.top + window.scrollY + rect.height / 2;
        const distance = Math.abs(nodeCenter - centerY);
        
        if (distance < bestDistance) {
          bestDistance = distance;
          bestNode = currentNode;
        }
      }
    }

    if (bestNode) {
      // Extract context around the current reading position
      const paragraph = bestNode.parentElement;
      const fullText = paragraph ? paragraph.textContent : bestNode.textContent;
      
      return {
        text: fullText.trim(),
        element: paragraph || bestNode.parentElement,
        scrollPosition: scrollTop,
        viewportCenter: centerY
      };
    }

    return null;
  };

  const extractContextAroundPosition = () => {
    if (!currentReadingPosition) {
      // Fallback: get text from current viewport
      const elements = document.querySelectorAll('p, div, span');
      let visibleText = '';
      
      elements.forEach(el => {
        const rect = el.getBoundingClientRect();
        if (rect.top >= 0 && rect.bottom <= window.innerHeight) {
          visibleText += el.textContent + ' ';
        }
      });
      
      return visibleText.trim().slice(0, 1000); // Limit context size
    }

    return currentReadingPosition.text.slice(0, 1000); // Current paragraph/section
  };

  const initializeCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          width: 640, 
          height: 480,
          facingMode: 'user'
        } 
      });
      
      streamRef.current = stream;
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setCameraPermission(true);
        
        // Start analyzing every 12 seconds (much less frequent)
        intervalRef.current = setInterval(analyzeConfusion, 12000);
      }
    } catch (error) {
      console.error('Camera access denied:', error);
      setCameraPermission(false);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const captureFrame = () => {
    if (!videoRef.current || !canvasRef.current) return null;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    ctx.drawImage(video, 0, 0);
    
    return canvas.toDataURL('image/jpeg', 0.8);
  };

  const analyzeConfusion = async () => {
    if (!currentText || isAnalyzing) return;

    setIsAnalyzing(true);
    
    try {
      const imageData = captureFrame();
      if (!imageData) return;

      // Get the specific text the user is currently reading
      const contextText = extractContextAroundPosition();
      
      const response = await axios.post(`${API_BASE_URL}/detect-confusion`, {
        image_data: imageData,
        current_text: contextText || currentText, // Use contextual text if available
        reading_position: currentReadingPosition || { paragraph: 0, sentence: 0 },
        full_context: currentText // Still send full context for broader understanding
      });

      const confusion = response.data;
      setConfusionData(confusion);
      
      console.log('Confusion detection result:', confusion);

      // Only trigger alerts when confusion is actually detected (not just any level)
      if (confusion.confusion_detected && onConfusionDetected) {
        console.log('Triggering confusion alert with context:', contextText);
        // Include the specific context that caused confusion
        onConfusionDetected({
          ...confusion,
          contextText: contextText,
          readingPosition: currentReadingPosition
        });
      }

      // Only show suggestions panel for detected confusion
      if (confusion.confusion_detected) {
        setShowSuggestions(true);
        
        // Auto-dismiss suggestions after 10 seconds
        setTimeout(() => {
          setShowSuggestions(false);
        }, 10000);
      }

    } catch (error) {
      console.error('Error analyzing confusion:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const dismissSuggestions = () => {
    setShowSuggestions(false);
  };

  if (cameraPermission === false) {
    return (
      <div className="confusion-detector disabled">
        <div className="camera-disabled">
          <p>📷 Camera access needed for confusion detection</p>
          <button onClick={initializeCamera} className="enable-camera-btn">
            Enable Camera
          </button>
        </div>
      </div>
    );
  }

  if (!isActive) {
    return null;
  }

  return (
    <div className="confusion-detector">
      {/* Hidden video and canvas for capture */}
      <video 
        ref={videoRef} 
        autoPlay 
        muted 
        style={{ display: 'none' }}
      />
      <canvas 
        ref={canvasRef} 
        style={{ display: 'none' }}
      />

      {/* Confusion Status Indicator */}
      <div className="confusion-status">
        <div className={`status-indicator ${confusionData?.confusion_detected ? 'confused' : 'clear'}`}>
          <div className="status-icon">
            {isAnalyzing ? '🔍' : confusionData?.confusion_detected ? '😕' : '😊'}
          </div>
          <div className="status-text">
            {isAnalyzing ? 'Analyzing...' : 
             confusionData?.confusion_detected ? 'Confusion detected' : 'Following along well'}
          </div>
        </div>
        
        {confusionData && (
          <div className="confusion-metrics">
            <div className="metric">
              <span>Confusion Level</span>
              <div className="meter">
                <div 
                  className="meter-fill" 
                  style={{ 
                    width: `${confusionData.confusion_level * 100}%`,
                    backgroundColor: confusionData.confusion_level > 0.6 ? '#ff6b6b' : '#51cf66'
                  }}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Confusion Suggestions Popup */}
      {showSuggestions && confusionData?.suggestions && (
        <div className="confusion-suggestions">
          <div className="suggestions-header">
            <h4>💡 Helpful Suggestions</h4>
            <button onClick={dismissSuggestions} className="close-btn">×</button>
          </div>
          <div className="suggestions-list">
            {confusionData.suggestions.map((suggestion, index) => (
              <div key={index} className="suggestion-item">
                {suggestion}
              </div>
            ))}
          </div>
          <div className="suggestions-actions">
            <button onClick={dismissSuggestions} className="dismiss-btn">
              Got it!
            </button>
          </div>
        </div>
      )}

      {/* Privacy Notice */}
      <div className="privacy-notice">
        <small>🔒 Camera data is processed locally and not stored</small>
      </div>
    </div>
  );
};

export default ConfusionDetector;
