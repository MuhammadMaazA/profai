import React, { useState, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import axios from 'axios';
import { CheckCircle, ArrowRight, ArrowLeft, RotateCcw, Trophy, Target } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

const PersonalizedQuiz = ({ chapterContent, chapterTitle, onQuizComplete }) => {
  const [quiz, setQuiz] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [userAnswers, setUserAnswers] = useState([]);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [quizResults, setQuizResults] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);  // Add submission state

  const generateQuiz = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/generate-quiz`, {
        chapter_content: chapterContent,
        chapter_title: chapterTitle,
        difficulty_preference: "mixed"
      });
      
      setQuiz(response.data);
      setUserAnswers(new Array(response.data.questions.length).fill(-1));
    } catch (error) {
      console.error('Error generating quiz:', error);
    } finally {
      setIsLoading(false);
    }
  }, [chapterContent, chapterTitle]);

  useEffect(() => {
    generateQuiz();
  }, [generateQuiz]);

  const handleAnswerSelect = (answerIndex) => {
    setSelectedAnswer(answerIndex);
  };

  const handleNextQuestion = () => {
    if (selectedAnswer === null) return;

    const newAnswers = [...userAnswers];
    newAnswers[currentQuestion] = selectedAnswer;
    setUserAnswers(newAnswers);
    setSelectedAnswer(null);

    if (currentQuestion < quiz.questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      submitQuiz(newAnswers);
    }
  };

  const handlePreviousQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
      setSelectedAnswer(userAnswers[currentQuestion - 1]);
    }
  };

  const submitQuiz = async (answers) => {
    if (isSubmitting) return; // Prevent double submission
    
    setIsSubmitting(true);
    setIsLoading(true);
    console.log('Submitting quiz with answers:', answers);
    console.log('Quiz data:', quiz);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/submit-quiz`, {
        quiz_id: quiz.quiz_id,
        user_answers: answers,
        questions: quiz.questions
      });
      
      console.log('Quiz submission response:', response.data);
      setQuizResults(response.data);
      setShowResults(true);
      
      if (onQuizComplete) {
        onQuizComplete(response.data);
      }
    } catch (error) {
      console.error('Error submitting quiz:', error);
      console.error('Error response:', error.response?.data);
      
      // Show error message to user
      alert(`Failed to submit quiz: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsLoading(false);
      setIsSubmitting(false);
    }
  };

  const resetQuiz = () => {
    setCurrentQuestion(0);
    setUserAnswers(new Array(quiz.questions.length).fill(-1));
    setSelectedAnswer(null);
    setShowResults(false);
    setQuizResults(null);
    setIsSubmitting(false);  // Reset submission state
  };

  if (isLoading) {
    return (
      <div className="quiz-container">
        <div className="quiz-loading">
          <div className="loading-spinner"></div>
          <p>Generating personalized quiz...</p>
        </div>
      </div>
    );
  }

  if (!quiz) {
    return (
      <div className="quiz-container">
        <div className="quiz-error">
          <p>Unable to generate quiz. Please try again.</p>
          <button onClick={generateQuiz} className="retry-button">
            🔄 Retry
          </button>
        </div>
      </div>
    );
  }

  if (showResults && quizResults) {
    const getScoreEmoji = () => {
      if (quizResults.percentage >= 90) return '🏆';
      if (quizResults.percentage >= 80) return '🎉';
      if (quizResults.percentage >= 70) return '👏';
      if (quizResults.percentage >= 60) return '👍';
      return '💪';
    };

    const getScoreClass = () => {
      if (quizResults.percentage >= 80) return 'score-excellent';
      if (quizResults.percentage >= 70) return 'score-good';
      return 'score-needs-improvement';
    };

    return (
      <div className="quiz-results-modal">
        <div className="quiz-results-content">
          <button className="close-modal-btn" onClick={() => setShowResults(false)}>
            ×
          </button>
          
          <div className="results-header">
            <span className="results-emoji">{getScoreEmoji()}</span>
            <h2 className="results-title">Quiz Complete!</h2>
            <div className={`results-score ${getScoreClass()}`}>
              {quizResults.percentage}%
            </div>
            <p className="results-percentage">
              {quizResults.correct_answers} out of {quizResults.total_questions} questions correct
            </p>
          </div>

          <div className="results-breakdown">
            {quizResults.strong_concepts && quizResults.strong_concepts.length > 0 && (
              <div className="breakdown-section">
                <h4 className="breakdown-title">
                  <CheckCircle size={20} style={{ color: 'var(--success-600)' }} />
                  Strong Concepts
                </h4>
                <div className="concept-list">
                  {quizResults.strong_concepts.map((concept, index) => (
                    <span key={index} className="concept-tag strong">{concept}</span>
                  ))}
                </div>
              </div>
            )}

            {quizResults.weak_concepts && quizResults.weak_concepts.length > 0 && (
              <div className="breakdown-section">
                <h4 className="breakdown-title">
                  <Target size={20} style={{ color: 'var(--error-600)' }} />
                  Areas for Improvement
                </h4>
                <div className="concept-list">
                  {quizResults.weak_concepts.map((concept, index) => (
                    <span key={index} className="concept-tag weak">{concept}</span>
                  ))}
                </div>
              </div>
            )}

            {quizResults.recommendations && quizResults.recommendations.length > 0 && (
              <div className="breakdown-section">
                <h4 className="breakdown-title">
                  💡 Recommendations
                </h4>
                <ul style={{ margin: '0 0 0 1rem', color: 'var(--secondary-700)' }}>
                  {quizResults.recommendations.map((rec, index) => (
                    <li key={index} style={{ marginBottom: '0.5rem' }}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="results-actions">
            <button onClick={resetQuiz} className="quiz-btn secondary">
              <RotateCcw size={16} />
              Retake Quiz
            </button>
            <button onClick={() => onQuizComplete(quizResults)} className="quiz-btn primary">
              <Trophy size={16} />
              Continue Learning
            </button>
          </div>
        </div>
      </div>
    );
  }

  const question = quiz.questions[currentQuestion];
  const progress = ((currentQuestion + 1) / quiz.questions.length) * 100;

  return (
    <div className="quiz-section">
      <div className="quiz-header">
        <h2>📝 {chapterTitle} - Quiz</h2>
        <div className="quiz-progress">
          <span className="progress-text">
            Question {currentQuestion + 1} of {quiz.questions.length}
          </span>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }}></div>
          </div>
        </div>
      </div>

      <div className="quiz-question">
        <div className="question-number">{currentQuestion + 1}</div>
        
        <div className="question-text">
          <ReactMarkdown>{question.question}</ReactMarkdown>
        </div>

        <div className="quiz-options">
          {question.options.map((option, index) => (
            <button
              key={index}
              className={`quiz-option ${selectedAnswer === index ? 'selected' : ''}`}
              onClick={() => handleAnswerSelect(index)}
            >
              <span className="option-letter">{String.fromCharCode(65 + index)}</span>
              <span className="option-text">{option}</span>
            </button>
          ))}
        </div>

        <div className="quiz-actions">
          <div className="quiz-nav-buttons">
            <button 
              onClick={handlePreviousQuestion}
              disabled={currentQuestion === 0}
              className="quiz-btn secondary"
            >
              <ArrowLeft size={16} />
              Previous
            </button>
          </div>
          
          <button 
            onClick={handleNextQuestion}
            disabled={selectedAnswer === null || isSubmitting}
            className="quiz-btn primary"
          >
            {currentQuestion === quiz.questions.length - 1 ? (
              isSubmitting ? 'Submitting...' : 'Submit Quiz'
            ) : (
              <>
                Next
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default PersonalizedQuiz;
