import React, { useState, useRef, useEffect } from 'react';
import { Play, Save, Download, Upload, RotateCcw, Copy, CheckCircle } from 'lucide-react';

const CODE_TEMPLATES = {
  python_basic: {
    name: 'Python Basics',
    code: `# Welcome to ProfAI Code Playground
# Let's start with some basic Python concepts

# Variables and data types
name = "AI Student"
age = 25
is_learning = True

print(f"Hello, {name}! You are {age} years old.")
print(f"Are you learning AI? {is_learning}")

# Let's try some AI-related calculations
import math

# Simple neural network activation function
def sigmoid(x):
    return 1 / (1 + math.exp(-x))

# Test the sigmoid function
inputs = [-2, -1, 0, 1, 2]
for x in inputs:
    result = sigmoid(x)
    print(f"sigmoid({x}) = {result:.4f}")
`
  },
  langchain_simple: {
    name: 'LangChain Basics',
    code: `# LangChain Basic Example
# This would normally require API keys and installations

# Simulated LangChain-style code structure
class SimpleChain:
    def __init__(self, prompt_template):
        self.prompt_template = prompt_template
    
    def run(self, **kwargs):
        # Simulate AI response generation
        prompt = self.prompt_template.format(**kwargs)
        return f"AI Response to: {prompt}"

# Create a simple educational chain
educational_chain = SimpleChain(
    "Explain the concept of {topic} in simple terms for a {level} student."
)

# Test the chain
topics = ["machine learning", "neural networks", "deep learning"]
for topic in topics:
    response = educational_chain.run(topic=topic, level="beginner")
    print(f"Topic: {topic}")
    print(f"Response: {response}")
    print("-" * 50)
`
  },
  ml_example: {
    name: 'ML Example',
    code: `# Simple Machine Learning Example
# Demonstrating basic concepts without external libraries

import random
import math

# Generate sample data for linear regression
def generate_linear_data(n_samples=100):
    data = []
    for _ in range(n_samples):
        x = random.uniform(0, 10)
        # y = 2x + 1 + noise
        y = 2 * x + 1 + random.uniform(-1, 1)
        data.append((x, y))
    return data

# Simple linear regression implementation
class LinearRegression:
    def __init__(self):
        self.slope = 0
        self.intercept = 0
    
    def fit(self, data):
        n = len(data)
        sum_x = sum(point[0] for point in data)
        sum_y = sum(point[1] for point in data)
        sum_xy = sum(point[0] * point[1] for point in data)
        sum_x2 = sum(point[0] ** 2 for point in data)
        
        self.slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        self.intercept = (sum_y - self.slope * sum_x) / n
    
    def predict(self, x):
        return self.slope * x + self.intercept

# Test the model
data = generate_linear_data()
model = LinearRegression()
model.fit(data)

print(f"Model parameters:")
print(f"Slope: {model.slope:.4f}")
print(f"Intercept: {model.intercept:.4f}")

# Make predictions
test_values = [1, 3, 5, 7, 9]
for x in test_values:
    prediction = model.predict(x)
    print(f"x={x}, predicted y={prediction:.4f}")
`
  }
};

const CodePlayground = ({ lesson, onComplete }) => {
  const [code, setCode] = useState('');
  const [output, setOutput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState('python_basic');
  const [savedCodes, setSavedCodes] = useState({});
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [saveFileName, setSaveFileName] = useState('');
  const textareaRef = useRef(null);

  useEffect(() => {
    // Load the selected template when component mounts or template changes
    setCode(CODE_TEMPLATES[selectedTemplate].code);
  }, [selectedTemplate]);

  const runCode = async () => {
    setIsRunning(true);
    setOutput('Running code...\n');

    try {
      // Simulate code execution with a delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // In a real implementation, this would send the code to a backend service
      // that can safely execute Python code in a sandboxed environment
      
      // For now, we'll simulate output based on code content
      const simulatedOutput = simulateCodeExecution(code);
      setOutput(simulatedOutput);
      
      // Mark lesson as completed if this is part of a lesson
      if (lesson && onComplete) {
        onComplete();
      }
    } catch (error) {
      setOutput(`Error: ${error.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  const simulateCodeExecution = (code) => {
    // Simple simulation of code execution
    const lines = code.split('\n');
    let output = '';
    
    // Look for print statements and simulate their output
    lines.forEach((line, index) => {
      if (line.trim().startsWith('print(')) {
        const printContent = line.match(/print\((.*)\)/);
        if (printContent && printContent[1]) {
          // Very basic evaluation of print statements
          let content = printContent[1];
          
          // Handle f-strings (very basic simulation)
          if (content.includes('f"') || content.includes("f'")) {
            content = content.replace(/f["'](.+?)["']/, '$1');
            content = content.replace(/{([^}]+)}/g, '[value]');
          }
          
          // Remove quotes
          content = content.replace(/["']/g, '');
          
          output += `${content}\n`;
        }
      }
      
      // Simulate some computational results
      if (line.includes('sigmoid(')) {
        const match = line.match(/sigmoid\((-?\d+)\)/);
        if (match) {
          const x = parseInt(match[1]);
          const result = 1 / (1 + Math.exp(-x));
          output += `sigmoid(${x}) = ${result.toFixed(4)}\n`;
        }
      }
    });
    
    if (output === '') {
      output = 'Code executed successfully! (No output to display)\nNote: This is a simulated environment. In production, code would execute in a secure sandbox.';
    }
    
    return output;
  };

  const saveCode = () => {
    if (saveFileName.trim()) {
      setSavedCodes(prev => ({
        ...prev,
        [saveFileName]: code
      }));
      setShowSaveDialog(false);
      setSaveFileName('');
    }
  };

  const loadSavedCode = (fileName) => {
    if (savedCodes[fileName]) {
      setCode(savedCodes[fileName]);
    }
  };

  const downloadCode = () => {
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'profai_code.py';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const resetCode = () => {
    setCode(CODE_TEMPLATES[selectedTemplate].code);
    setOutput('');
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(code);
  };

  return (
    <div className="code-playground">
      <div className="playground-header">
        <h3>Interactive Code Playground</h3>
        <div className="playground-controls">
          <select 
            value={selectedTemplate}
            onChange={(e) => setSelectedTemplate(e.target.value)}
            className="template-selector"
          >
            {Object.entries(CODE_TEMPLATES).map(([key, template]) => (
              <option key={key} value={key}>{template.name}</option>
            ))}
          </select>
          
          <button className="btn-secondary" onClick={resetCode}>
            <RotateCcw size={16} />
            Reset
          </button>
          
          <button className="btn-secondary" onClick={copyToClipboard}>
            <Copy size={16} />
            Copy
          </button>
          
          <button className="btn-secondary" onClick={() => setShowSaveDialog(true)}>
            <Save size={16} />
            Save
          </button>
          
          <button className="btn-secondary" onClick={downloadCode}>
            <Download size={16} />
            Download
          </button>
        </div>
      </div>

      <div className="playground-content">
        <div className="code-editor">
          <div className="editor-header">
            <span>Code Editor</span>
            <div className="editor-actions">
              <button 
                className="btn-primary" 
                onClick={runCode}
                disabled={isRunning}
              >
                <Play size={16} />
                {isRunning ? 'Running...' : 'Run Code'}
              </button>
            </div>
          </div>
          
          <textarea
            ref={textareaRef}
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="code-textarea"
            placeholder="Write your Python code here..."
            spellCheck={false}
          />
        </div>

        <div className="output-panel">
          <div className="output-header">
            <span>Output</span>
            {lesson && onComplete && (
              <button className="btn-success" onClick={onComplete}>
                <CheckCircle size={16} />
                Mark Complete
              </button>
            )}
          </div>
          
          <pre className="output-content">
            {output || 'Click "Run Code" to see output here...'}
          </pre>
        </div>
      </div>

      {/* Saved Codes Panel */}
      {Object.keys(savedCodes).length > 0 && (
        <div className="saved-codes">
          <h4>Saved Code Snippets</h4>
          <div className="saved-codes-list">
            {Object.keys(savedCodes).map(fileName => (
              <div key={fileName} className="saved-code-item">
                <span>{fileName}</span>
                <button 
                  className="btn-small"
                  onClick={() => loadSavedCode(fileName)}
                >
                  Load
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Save Dialog */}
      {showSaveDialog && (
        <div className="modal-overlay">
          <div className="modal">
            <h4>Save Code Snippet</h4>
            <input
              type="text"
              placeholder="Enter file name..."
              value={saveFileName}
              onChange={(e) => setSaveFileName(e.target.value)}
              className="save-input"
            />
            <div className="modal-actions">
              <button 
                className="btn-secondary" 
                onClick={() => setShowSaveDialog(false)}
              >
                Cancel
              </button>
              <button 
                className="btn-primary" 
                onClick={saveCode}
                disabled={!saveFileName.trim()}
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Code Tips */}
      <div className="code-tips">
        <h4>💡 Coding Tips:</h4>
        <ul>
          <li>Experiment with the provided examples</li>
          <li>Try modifying variables and parameters</li>
          <li>Add your own print statements to understand the flow</li>
          <li>Save interesting code snippets for later reference</li>
        </ul>
      </div>
    </div>
  );
};

export default CodePlayground;
