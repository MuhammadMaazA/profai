import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BookOpen, Clock, Trophy, ChevronRight, PlayCircle, CheckCircle, Star, Target, Users, TrendingUp } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

const CurriculumBrowser = () => {
  const [curricula, setCurricula] = useState({});
  const [selectedCurriculum, setSelectedCurriculum] = useState(null);
  const [currentLesson, setCurrentLesson] = useState(null);
  const [lessonProgress, setLessonProgress] = useState({});
  const [userProgress, setUserProgress] = useState({});
  const [activeSection, setActiveSection] = useState('overview');

  useEffect(() => {
    loadCurricula();
  }, []);

  const loadCurricula = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/curriculum`);
      setCurricula(response.data.curricula);
    } catch (err) {
      console.error('Error loading curricula:', err);
    }
  };

  const loadLesson = async (lessonId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/lessons/${lessonId}`);
      setCurrentLesson({ ...response.data, id: lessonId });
      setActiveSection('lesson');
    } catch (err) {
      console.error('Error loading lesson:', err);
    }
  };

  const updateProgress = async (lessonId, progressData) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/lessons/${lessonId}/progress`, progressData);
      setLessonProgress(prev => ({ ...prev, [lessonId]: response.data.progress }));
    } catch (err) {
      console.error('Error updating progress:', err);
    }
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case 'beginner': return '#10b981';
      case 'intermediate': return '#f59e0b'; 
      case 'advanced': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getDifficultyIcon = (difficulty) => {
    switch (difficulty) {
      case 'beginner': return '🌱';
      case 'intermediate': return '🔥';
      case 'advanced': return '⚡';
      default: return '📚';
    }
  };

  if (activeSection === 'lesson' && currentLesson) {
    return (
      <div className="curriculum-lesson-viewer">
        <div className="lesson-header">
          <button 
            className="back-button"
            onClick={() => setActiveSection('curriculum')}
          >
            ← Back to Curriculum
          </button>
          <div className="lesson-meta">
            <h1>{currentLesson.id.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</h1>
            <div className="lesson-info">
              <span className="duration">
                <Clock size={16} />
                {currentLesson.estimated_time} min
              </span>
            </div>
          </div>
        </div>

        <div className="lesson-content">
          <div className="lesson-section">
            <h2>Introduction</h2>
            <div className="content-block">
              {currentLesson.introduction}
            </div>
          </div>

          {currentLesson.main_content.map((content, index) => (
            <div key={index} className="lesson-section">
              <h2>{content.title}</h2>
              <div className={`content-block content-${content.type}`}>
                <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
                  {content.content}
                </pre>
              </div>
            </div>
          ))}

          {currentLesson.examples.length > 0 && (
            <div className="lesson-section">
              <h2>Examples</h2>
              {currentLesson.examples.map((example, index) => (
                <div key={index} className="example-block">
                  <h3>{example.title}</h3>
                  <p>{example.description}</p>
                </div>
              ))}
            </div>
          )}

          {currentLesson.exercises.length > 0 && (
            <div className="lesson-section">
              <h2>Practice Exercises</h2>
              {currentLesson.exercises.map((exercise, index) => (
                <div key={index} className="exercise-block">
                  <h3>Exercise {index + 1}</h3>
                  <p><strong>Question:</strong> {exercise.question}</p>
                  {exercise.hints && (
                    <details>
                      <summary>💡 Hints</summary>
                      <ul>
                        {exercise.hints.map((hint, hintIndex) => (
                          <li key={hintIndex}>{hint}</li>
                        ))}
                      </ul>
                    </details>
                  )}
                  {exercise.sample_answer && (
                    <details>
                      <summary>📝 Sample Answer</summary>
                      <p>{exercise.sample_answer}</p>
                    </details>
                  )}
                </div>
              ))}
            </div>
          )}

          <div className="lesson-section">
            <h2>Summary</h2>
            <div className="content-block">
              <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
                {currentLesson.summary}
              </pre>
            </div>
          </div>

          {currentLesson.further_reading.length > 0 && (
            <div className="lesson-section">
              <h2>Further Reading</h2>
              <ul className="reading-list">
                {currentLesson.further_reading.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="lesson-actions">
          <button 
            className="complete-lesson-btn"
            onClick={() => {
              updateProgress(currentLesson.id, { 
                completed_sections: ['all'], 
                completion_time: currentLesson.estimated_time 
              });
              setActiveSection('curriculum');
            }}
          >
            <CheckCircle size={16} />
            Mark as Complete
          </button>
        </div>
      </div>
    );
  }

  if (activeSection === 'curriculum' && selectedCurriculum) {
    const curriculum = curricula[selectedCurriculum];
    return (
      <div className="curriculum-detail">
        <div className="curriculum-header">
          <button 
            className="back-button"
            onClick={() => setActiveSection('overview')}
          >
            ← Back to All Curricula
          </button>
          <div className="curriculum-info">
            <h1>{curriculum.name}</h1>
            <p>{curriculum.description}</p>
            <div className="curriculum-stats">
              <span className="stat">
                <BookOpen size={16} />
                {curriculum.lessons.length} Lessons
              </span>
              <span className="stat">
                <Clock size={16} />
                {curriculum.total_duration} minutes
              </span>
            </div>
          </div>
        </div>

        <div className="lesson-list">
          {curriculum.lessons.map((lessonId, index) => {
            const difficulty = curriculum.difficulty_progression[index];
            const isCompleted = lessonProgress[lessonId]?.completion_percentage === 100;
            
            return (
              <div key={lessonId} className={`lesson-card ${isCompleted ? 'completed' : ''}`}>
                <div className="lesson-number">
                  {isCompleted ? <CheckCircle size={20} /> : index + 1}
                </div>
                <div className="lesson-info">
                  <h3>{lessonId.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</h3>
                  <div className="lesson-meta">
                    <span 
                      className="difficulty" 
                      style={{ color: getDifficultyColor(difficulty) }}
                    >
                      {getDifficultyIcon(difficulty)} {difficulty}
                    </span>
                  </div>
                </div>
                <button 
                  className="start-lesson-btn"
                  onClick={() => loadLesson(lessonId)}
                >
                  <PlayCircle size={16} />
                  {isCompleted ? 'Review' : 'Start'}
                </button>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="curriculum-browser">
      <div className="curriculum-header">
        <h1>🎓 AI Learning Curricula</h1>
        <p>Structured learning paths from beginner to advanced AI mastery</p>
      </div>

      <div className="curricula-grid">
        {Object.entries(curricula).map(([curriculumId, curriculum]) => (
          <div key={curriculumId} className="curriculum-card">
            <div className="curriculum-icon">
              {curriculumId.includes('theory') ? '🧠' : 
               curriculumId.includes('practical') ? '🔧' : '🚀'}
            </div>
            <div className="curriculum-content">
              <h2>{curriculum.name}</h2>
              <p>{curriculum.description}</p>
              
              <div className="curriculum-stats">
                <div className="stat">
                  <BookOpen size={16} />
                  <span>{curriculum.lessons.length} lessons</span>
                </div>
                <div className="stat">
                  <Clock size={16} />
                  <span>{Math.round(curriculum.total_duration / 60)}h {curriculum.total_duration % 60}m</span>
                </div>
                <div className="stat">
                  <Target size={16} />
                  <span>{curriculum.difficulty_progression[0]} → {curriculum.difficulty_progression[curriculum.difficulty_progression.length - 1]}</span>
                </div>
              </div>

              <div className="difficulty-progression">
                {curriculum.difficulty_progression.map((difficulty, index) => (
                  <span 
                    key={index}
                    className="difficulty-indicator"
                    style={{ backgroundColor: getDifficultyColor(difficulty) }}
                    title={`Lesson ${index + 1}: ${difficulty}`}
                  ></span>
                ))}
              </div>
            </div>
            
            <button 
              className="start-curriculum-btn"
              onClick={() => {
                setSelectedCurriculum(curriculumId);
                setActiveSection('curriculum');
              }}
            >
              <ChevronRight size={16} />
              Start Learning
            </button>
          </div>
        ))}
      </div>

      <div className="features-section">
        <h2>🌟 Why Choose Our Curricula?</h2>
        <div className="features-grid">
          <div className="feature">
            <Users size={24} />
            <h3>Expert-Designed</h3>
            <p>Created by AI professionals with industry experience</p>
          </div>
          <div className="feature">
            <TrendingUp size={24} />
            <h3>Progressive Learning</h3>
            <p>Carefully structured from basics to advanced concepts</p>
          </div>
          <div className="feature">
            <Trophy size={24} />
            <h3>Practical Focus</h3>
            <p>Real-world projects and hands-on exercises</p>
          </div>
          <div className="feature">
            <Star size={24} />
            <h3>Self-Paced</h3>
            <p>Learn at your own speed with progress tracking</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CurriculumBrowser;
