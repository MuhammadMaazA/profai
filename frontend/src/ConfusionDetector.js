import React, { useState, useRef, useEffect, useCallback } from 'react';
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

  // Define all callback functions first
  const getCurrentReadingPosition = useCallback(() => {
    if (!contentRef || !contentRef.current) return null;

    const contentElement = contentRef.current;
    const viewportHeight = window.innerHeight;
    const scrollTop = window.scrollY;
    
    // Find the element that's currently in the center of the viewport
    const centerY = scrollTop + viewportHeight / 2;
    
    // Create a text walker to find readable text nodes
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
      const text = bestNode.textContent;
      const rect = bestNode.parentElement.getBoundingClientRect();
      
      return {
        text: text,
        element: bestNode.parentElement,
        position: {
          top: rect.top + window.scrollY,
          height: rect.height
        }
      };
    }

    return null;
  }, [contentRef]);

  const getVisibleContext = useCallback(() => {
    if (!currentText) {
      // If no explicit current text, try to get context from visible area
      const visibleText = getVisibleTextContent();
      
      return visibleText.trim().slice(0, 1000); // Limit context size
    }

    return currentReadingPosition?.text?.slice(0, 1000) || ''; // Current paragraph/section
  }, [currentText, currentReadingPosition]);

  const getVisibleTextContent = useCallback(() => {
    if (!contentRef || !contentRef.current) return '';
    
    const element = contentRef.current;
    const rect = element.getBoundingClientRect();
    const viewportHeight = window.innerHeight;
    
    // Get text that's currently visible in viewport
    if (rect.top < viewportHeight && rect.bottom > 0) {
      return element.textContent || '';
    }
    
    return '';
  }, [contentRef]);

  const initializeCamera = useCallback(async () => {
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
        intervalRef.current = setInterval(() => {
          analyzeConfusion();
        }, 12000);
      }
    } catch (error) {
      console.error('Camera access denied:', error);
      setCameraPermission(false);
    }
  }, []);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setCameraPermission(null);
  }, []);

  const startPositionTracking = useCallback(() => {
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
  }, [contentRef, getCurrentReadingPosition]);

  const stopPositionTracking = useCallback(() => {
    if (window.scrollCleanup) {
      window.scrollCleanup();
      delete window.scrollCleanup;
    }
  }, []);

  const captureFrame = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return null;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    ctx.drawImage(video, 0, 0);
    
    return canvas.toDataURL('image/jpeg', 0.8);
  }, []);

  const analyzeConfusion = useCallback(async () => {
    if (isAnalyzing || !isActive) return;

    setIsAnalyzing(true);

    try {
      const frameData = captureFrame();
      const context = getVisibleContext();
      
      if (!frameData || !context) {
        setIsAnalyzing(false);
        return;
      }

      const response = await axios.post(`${API_BASE_URL}/detect-confusion`, {
        frame_data: frameData,
        context_text: context,
        reading_position: currentReadingPosition
      });

      const data = response.data;
      setConfusionData(data);

      // Trigger callback if confusion detected
      if (data.confusion_detected && data.confidence > 0.7) {
        setShowSuggestions(true);
        if (onConfusionDetected) {
          onConfusionDetected({
            type: 'confusion',
            confidence: data.confidence,
            suggestions: data.suggestions,
            context: context
          });
        }
      }

    } catch (error) {
      console.error('Error analyzing confusion:', error);
    } finally {
      setIsAnalyzing(false);
    }
  }, [isAnalyzing, isActive, captureFrame, getVisibleContext, currentReadingPosition, onConfusionDetected]);

  // Main useEffect after all functions are defined
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
  }, [isActive, initializeCamera, startPositionTracking, stopCamera, stopPositionTracking]);

  const dismissSuggestions = () => {
    setShowSuggestions(false);
    setConfusionData(null);
  };

  if (!isActive) {
    return null;
  }

  return (
    <div className="confusion-detector">
      <div className="camera-container" style={{ display: 'none' }}>
        <video 
          ref={videoRef} 
          autoPlay 
          muted 
          playsInline
          style={{ width: '160px', height: '120px' }}
        />
        <canvas ref={canvasRef} style={{ display: 'none' }} />
      </div>

      {cameraPermission === false && (
        <div className="camera-permission-request">
          <div className="permission-message">
            <h4>🎥 Camera Access Needed</h4>
            <p>We use your camera to detect confusion and provide personalized help.</p>
            <button onClick={initializeCamera} className="enable-camera-btn">
              Enable Camera
            </button>
          </div>
        </div>
      )}

      {showSuggestions && confusionData && (
        <div className="confusion-suggestions">
          <div className="suggestion-header">
            <h4>💡 Need Help?</h4>
            <button onClick={dismissSuggestions} className="dismiss-btn">×</button>
          </div>
          <div className="suggestion-content">
            <p>You seem confused about this section. Here are some suggestions:</p>
            {confusionData.suggestions && confusionData.suggestions.map((suggestion, index) => (
              <div key={index} className="suggestion-item">
                <span className="suggestion-text">{suggestion}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {isAnalyzing && (
        <div className="analyzing-indicator">
          <span>🧠 Analyzing...</span>
        </div>
      )}
    </div>
  );
};

export default ConfusionDetector;
