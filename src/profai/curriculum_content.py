"""
ProfAI Curriculum Content System
Contains actual lesson content, structured curricula, and adaptive learning logic
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path


@dataclass
class LessonContent:
    """Actual lesson content with rich media and interactive elements"""
    introduction: str
    main_content: List[Dict[str, Any]]  # Structured content blocks
    examples: List[Dict[str, Any]]
    exercises: List[Dict[str, Any]]
    summary: str
    further_reading: List[str]
    estimated_time: int  # minutes


@dataclass
class CurriculumPath:
    """Complete curriculum with ordered lessons and dependencies"""
    name: str
    description: str
    lessons: List[str]  # lesson IDs in order
    total_duration: int  # minutes
    difficulty_progression: List[str]  # beginner -> intermediate -> advanced


# LESSON CONTENT DATABASE
LESSON_CONTENTS = {
    "ai_fundamentals": LessonContent(
        introduction="""
        Welcome to AI Fundamentals! 🤖 
        
        In this lesson, we'll explore what AI really is, dispel common myths, and understand 
        the different types of AI systems we interact with daily. By the end, you'll have 
        a clear foundation to build upon.
        """,
        main_content=[
            {
                "type": "concept",
                "title": "What is Artificial Intelligence?",
                "content": """
                AI is the simulation of human intelligence in machines. Think of it as creating 
                systems that can perceive, reason, learn, and act in ways that would normally 
                require human-level intelligence.
                
                Key characteristics:
                • **Perception**: Understanding inputs (text, images, sound)
                • **Reasoning**: Making logical connections and decisions  
                • **Learning**: Improving performance through experience
                • **Action**: Taking steps to achieve goals
                """
            },
            {
                "type": "comparison",
                "title": "Types of AI: Narrow vs General",
                "content": """
                **Narrow AI (ANI)** - Current Reality:
                • Excels at specific tasks (chess, image recognition, language translation)
                • Cannot transfer knowledge between domains
                • Examples: Siri, ChatGPT, recommendation systems
                
                **General AI (AGI)** - Future Goal:
                • Human-level intelligence across all domains
                • Can learn and apply knowledge flexibly
                • Currently theoretical, no existing examples
                
                **Super AI (ASI)** - Speculative Future:
                • Exceeds human intelligence in all areas
                • Highly speculative and controversial topic
                """
            },
            {
                "type": "real_world",
                "title": "AI in Your Daily Life",
                "content": """
                You interact with AI more than you realize:
                
                🔍 **Search Engines**: Google's ranking algorithms
                🛒 **E-commerce**: Amazon's product recommendations  
                🚗 **Transportation**: GPS route optimization, ride-sharing
                📱 **Social Media**: Content feeds, photo tagging
                💬 **Communication**: Spam filters, auto-complete, translation
                🎵 **Entertainment**: Spotify playlists, Netflix suggestions
                """
            }
        ],
        examples=[
            {
                "title": "ChatGPT vs Human Intelligence",
                "description": "ChatGPT can write poetry, code, and essays but can't tie shoes or make coffee. This illustrates narrow AI - superhuman in text but limited to that domain."
            },
            {
                "title": "Tesla Autopilot",
                "description": "Advanced AI for driving but can't help you with your taxes. Domain-specific intelligence."
            }
        ],
        exercises=[
            {
                "type": "reflection",
                "question": "List 3 AI systems you used today. For each, identify what type of intelligence it demonstrates.",
                "sample_answer": "1. Google Search - Information retrieval and ranking, 2. Phone keyboard - Predictive text, 3. Spotify - Pattern recognition for music preferences"
            },
            {
                "type": "analysis",
                "question": "Why don't we have AGI yet? What are the main challenges?",
                "hints": ["Think about consciousness, reasoning, transfer learning, common sense"]
            }
        ],
        summary="""
        **Key Takeaways:**
        • AI simulates human intelligence in machines
        • Current AI is 'narrow' - excellent at specific tasks but limited
        • General AI (human-level across all domains) doesn't exist yet
        • You interact with narrow AI systems daily
        • Understanding AI types helps set realistic expectations
        """,
        further_reading=[
            "Stuart Russell's 'Human Compatible' - AI alignment and safety",
            "Nick Bostrom's 'Superintelligence' - Long-term AI implications",
            "Andrew Ng's AI for Everyone course - Practical AI applications"
        ],
        estimated_time=15
    ),
    
    "machine_learning_basics": LessonContent(
        introduction="""
        Machine Learning Demystified! 📊
        
        ML is the engine behind most modern AI. Instead of programming explicit rules, 
        we teach computers to find patterns in data. Let's explore the three main 
        approaches and when to use each.
        """,
        main_content=[
            {
                "type": "concept",
                "title": "Machine Learning Core Idea",
                "content": """
                Traditional Programming: Rules + Data → Answers
                Machine Learning: Data + Answers → Rules
                
                Instead of writing code for every scenario, we show the computer examples 
                and let it discover the underlying patterns. The computer 'learns' rules 
                from examples.
                """
            },
            {
                "type": "framework",
                "title": "Three Types of Machine Learning",
                "content": """
                **1. Supervised Learning** 📚
                • Learn from labeled examples
                • Like studying with answer key
                • Examples: Email spam detection, medical diagnosis
                • Input-output pairs: (email content, spam/not spam)
                
                **2. Unsupervised Learning** 🔍  
                • Find hidden patterns without labels
                • Like discovering customer segments
                • Examples: Market research, gene analysis
                • Just input data, no 'correct' answers
                
                **3. Reinforcement Learning** 🎮
                • Learn through trial and error with rewards
                • Like training a pet with treats
                • Examples: Game AI, robotics, trading
                • Agent takes actions, gets feedback
                """
            },
            {
                "type": "practical",
                "title": "The Data Pipeline",
                "content": """
                **Training Data** (70%): Teach the model
                **Validation Data** (15%): Tune and improve  
                **Test Data** (15%): Final evaluation
                
                Why split? To avoid 'overfitting' - memorizing instead of learning.
                Like studying - you need practice problems AND a final exam.
                """
            }
        ],
        examples=[
            {
                "title": "Netflix Recommendations",
                "description": "Supervised: User ratings → Movie preferences. Unsupervised: Find viewer segments. Reinforcement: Optimize viewing time through A/B testing."
            },
            {
                "title": "Self-Driving Cars", 
                "description": "Supervised: Camera images → Object detection. Unsupervised: Traffic pattern analysis. Reinforcement: Optimal driving decisions."
            }
        ],
        exercises=[
            {
                "type": "classification",
                "question": "For each scenario, identify the ML type: A) Predicting house prices from features, B) Grouping customers by behavior, C) Training a robot to walk",
                "sample_answer": "A) Supervised (regression), B) Unsupervised (clustering), C) Reinforcement learning"
            },
            {
                "type": "design",
                "question": "Design an ML solution for detecting fake news. What type would you use and why?",
                "hints": ["Consider what data you have, what output you want, how you'd measure success"]
            }
        ],
        summary="""
        **Key Takeaways:**
        • ML learns patterns from data instead of explicit programming
        • Supervised: Learn from labeled examples (prediction)
        • Unsupervised: Find hidden patterns (discovery)  
        • Reinforcement: Learn through trial and error (optimization)
        • Always split data to avoid overfitting
        • Choose ML type based on your data and goals
        """,
        further_reading=[
            "Andrew Ng's Machine Learning Course - Stanford CS229",
            "Hands-On Machine Learning by Aurélien Géron",
            "Elements of Statistical Learning (advanced mathematics)"
        ],
        estimated_time=25
    ),
    
    "prompt_engineering": LessonContent(
        introduction="""
        Prompt Engineering: The Art of AI Communication! 🎯
        
        Large Language Models like GPT are incredibly powerful, but they need clear 
        instructions. Learn to craft prompts that consistently get you the results 
        you want - from creative writing to code generation.
        """,
        main_content=[
            {
                "type": "principle",
                "title": "The CLEAR Framework",
                "content": """
                **C**ontext: Provide relevant background
                **L**ength: Specify desired output length  
                **E**xamples: Show what you want (few-shot)
                **A**udience: Define target audience/style
                **R**ole: Assign the AI a specific role
                
                Example: "You are a Python expert (Role). Explain list comprehensions 
                (Context) to a beginner programmer (Audience) in 2-3 sentences (Length). 
                Here's the format: [concept] - [simple explanation] - [code example] (Examples)"
                """
            },
            {
                "type": "technique",
                "title": "Advanced Prompting Techniques", 
                "content": """
                **Chain-of-Thought**: Ask AI to show reasoning steps
                • "Think step by step to solve this math problem"
                
                **Few-Shot Learning**: Provide examples
                • "Translate English to French. English: Hello → French: Bonjour"
                
                **Role Playing**: Assign specific expertise
                • "You are a senior software engineer reviewing code..."
                
                **Template Prompts**: Reusable structures
                • "Analyze [TOPIC] from [PERSPECTIVE] for [AUDIENCE]"
                """
            },
            {
                "type": "optimization",
                "title": "Prompt Optimization Strategies",
                "content": """
                **Start Simple**: Begin with basic prompt, then iterate
                **Be Specific**: Vague prompts → Vague outputs
                **Use Constraints**: "In exactly 100 words..." 
                **Test Variations**: A/B test different phrasings
                **Add Context**: More background = better results
                **Specify Format**: JSON, bullet points, table, etc.
                """
            }
        ],
        examples=[
            {
                "title": "Bad vs Good Prompts",
                "description": """
                ❌ Bad: "Write about AI"
                ✅ Good: "Write a 200-word executive summary explaining how AI chatbots can reduce customer service costs for e-commerce companies, focusing on ROI metrics"
                """
            },
            {
                "title": "Code Generation",
                "description": """
                ❌ Bad: "Create a function"  
                ✅ Good: "Create a Python function that takes a list of dictionaries with 'name' and 'age' keys, filters for people over 18, and returns sorted by age. Include docstring and type hints."
                """
            }
        ],
        exercises=[
            {
                "type": "practice",
                "question": "Improve this prompt: 'Explain machine learning.' Make it specific for a marketing manager who wants to understand customer segmentation.",
                "sample_answer": "You are an AI consultant. Explain machine learning specifically for customer segmentation to a marketing manager with no technical background. Focus on business benefits, use simple analogies, and provide 2-3 real examples from retail/e-commerce. Keep it under 300 words."
            },
            {
                "type": "design",
                "question": "Create a template prompt for generating social media posts for any product.",
                "hints": ["Think about variables: product, platform, audience, tone, call-to-action"]
            }
        ],
        summary="""
        **Key Takeaways:**
        • Clear prompts get better results - use the CLEAR framework
        • Chain-of-thought prompting improves reasoning quality
        • Few-shot examples teach the AI your desired format
        • Role assignment leverages specialized knowledge
        • Iterate and test different prompt variations
        • Specificity beats vagueness every time
        """,
        further_reading=[
            "OpenAI Prompt Engineering Guide - Official best practices",
            "Prompt Engineering Guide by DAIR.AI - Comprehensive techniques", 
            "Learn Prompting - Interactive tutorials and examples"
        ],
        estimated_time=20
    ),
    
    "langchain_basics": LessonContent(
        introduction="""
        Building AI Agents with LangChain! 🔗
        
        LangChain is your toolkit for creating powerful AI applications. We'll build 
        a complete agent that can chat, remember conversations, and use external tools. 
        By the end, you'll have a working AI assistant!
        """,
        main_content=[
            {
                "type": "setup",
                "title": "Environment Setup",
                "content": """
                ```bash
                # Install LangChain and dependencies
                pip install langchain langchain-openai langchain-community
                pip install python-dotenv
                
                # Create .env file
                OPENAI_API_KEY=your_key_here
                ```
                
                **Core Concepts:**
                • **Chains**: Sequence operations (prompt → LLM → output)
                • **Agents**: Decision-making entities that use tools
                • **Memory**: Conversation history and context
                • **Tools**: External capabilities (search, calculator, APIs)
                """
            },
            {
                "type": "code_tutorial",
                "title": "Your First LangChain Application",
                "content": """
                ```python
                from langchain_openai import ChatOpenAI
                from langchain.schema import HumanMessage, SystemMessage
                from langchain.memory import ConversationBufferMemory
                from langchain.agents import initialize_agent, Tool
                from langchain.tools import DuckDuckGoSearchRun
                import os
                from dotenv import load_dotenv
                
                load_dotenv()
                
                # Initialize LLM
                llm = ChatOpenAI(temperature=0.7)
                
                # Create memory
                memory = ConversationBufferMemory(memory_key="chat_history")
                
                # Define tools
                search = DuckDuckGoSearchRun()
                tools = [
                    Tool(
                        name="Search",
                        func=search.run,
                        description="Search the internet for current information"
                    )
                ]
                
                # Create agent
                agent = initialize_agent(
                    tools=tools,
                    llm=llm,
                    agent="conversational-react-description",
                    memory=memory,
                    verbose=True
                )
                
                # Use the agent
                response = agent.run("What's the latest news about AI?")
                print(response)
                ```
                """
            },
            {
                "type": "architecture",
                "title": "LangChain Architecture Patterns",
                "content": """
                **Simple Chain**: Prompt → LLM → Output
                **Sequential Chain**: Multiple steps in sequence
                **Router Chain**: Dynamic routing based on input
                **Agent Pattern**: LLM decides which tools to use
                
                **Best Practices:**
                • Start simple, add complexity gradually
                • Use memory for conversational interfaces
                • Implement error handling and retries
                • Log agent decisions for debugging
                • Test with diverse inputs
                """
            }
        ],
        examples=[
            {
                "title": "Research Assistant Agent",
                "description": "Agent with search, calculator, and summary tools that can research topics and provide structured reports."
            },
            {
                "title": "Customer Service Bot",
                "description": "Conversational agent with access to FAQ database, order tracking, and escalation protocols."
            }
        ],
        exercises=[
            {
                "type": "coding",
                "question": "Extend the basic agent with a calculator tool. Test it by asking 'What's 15% of $250?'",
                "hints": ["Import LLMMathChain", "Add to tools list", "Test with math questions"]
            },
            {
                "type": "project",
                "question": "Design an agent that helps with cooking. What tools would it need?",
                "sample_answer": "Recipe search, nutrition calculator, timer, unit converter, ingredient substitution database"
            }
        ],
        summary="""
        **Key Takeaways:**
        • LangChain simplifies building AI applications
        • Agents can reason about which tools to use
        • Memory enables conversational interfaces
        • Start with simple chains, evolve to complex agents
        • Tools extend AI capabilities beyond text generation
        • Proper error handling is crucial for production
        """,
        further_reading=[
            "LangChain Documentation - Official guides and API reference",
            "LangChain Cookbook - Real-world application examples",
            "Building LLM Applications for Production - Deployment guide"
        ],
        estimated_time=30
    )
}

# CURRICULUM PATHS
CURRICULUM_PATHS = {
    "theory_fundamentals": CurriculumPath(
        name="AI Theory Fundamentals",
        description="Master the theoretical foundations of AI and machine learning",
        lessons=["ai_fundamentals", "machine_learning_basics", "prompt_engineering"],
        total_duration=60,
        difficulty_progression=["beginner", "beginner", "intermediate"]
    ),
    
    "practical_builder": CurriculumPath(
        name="Practical AI Builder",
        description="Learn to build real AI applications and deploy them",
        lessons=["langchain_basics", "huggingface_deployment", "ai_agent_architecture"],
        total_duration=105,
        difficulty_progression=["beginner", "intermediate", "advanced"]
    ),
    
    "complete_ai_mastery": CurriculumPath(
        name="Complete AI Mastery",
        description="Comprehensive journey from theory to advanced implementation",
        lessons=["ai_fundamentals", "machine_learning_basics", "prompt_engineering", 
                "langchain_basics", "neural_networks_implementation", "huggingface_deployment", 
                "ai_agent_architecture"],
        total_duration=200,
        difficulty_progression=["beginner", "beginner", "intermediate", "beginner", 
                               "intermediate", "intermediate", "advanced"]
    )
}


def get_lesson_content(lesson_id: str) -> Optional[LessonContent]:
    """Get full lesson content by ID"""
    return LESSON_CONTENTS.get(lesson_id)


def get_curriculum_path(path_id: str) -> Optional[CurriculumPath]:
    """Get curriculum path by ID"""
    return CURRICULUM_PATHS.get(path_id)


def get_available_curricula() -> Dict[str, CurriculumPath]:
    """Get all available curriculum paths"""
    return CURRICULUM_PATHS


def get_lesson_progress_data(lesson_id: str, user_progress: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate lesson progress and recommendations"""
    lesson = get_lesson_content(lesson_id)
    if not lesson:
        return {}
    
    completed_sections = user_progress.get('completed_sections', [])
    total_sections = len(lesson.main_content) + len(lesson.exercises)
    
    return {
        "lesson_id": lesson_id,
        "completion_percentage": (len(completed_sections) / total_sections) * 100,
        "estimated_time_remaining": lesson.estimated_time - (len(completed_sections) * 3),
        "next_section": _get_next_section(lesson, completed_sections),
        "difficulty_assessment": _assess_difficulty(user_progress),
        "personalized_tips": _get_personalized_tips(lesson, user_progress)
    }


def _get_next_section(lesson: LessonContent, completed: List[str]) -> Optional[str]:
    """Get the next section to study"""
    all_sections = [f"content_{i}" for i in range(len(lesson.main_content))] + \
                   [f"exercise_{i}" for i in range(len(lesson.exercises))]
    
    for section in all_sections:
        if section not in completed:
            return section
    return None


def _assess_difficulty(user_progress: Dict[str, Any]) -> str:
    """Assess if content is too easy/hard for user"""
    completion_time = user_progress.get('completion_time', 0)
    exercise_scores = user_progress.get('exercise_scores', [])
    
    if not exercise_scores:
        return "appropriate"
    
    avg_score = sum(exercise_scores) / len(exercise_scores)
    
    if avg_score > 90 and completion_time < 15:
        return "too_easy"
    elif avg_score < 60:
        return "too_hard" 
    else:
        return "appropriate"


def _get_personalized_tips(lesson: LessonContent, user_progress: Dict[str, Any]) -> List[str]:
    """Generate personalized learning tips"""
    tips = []
    difficulty = _assess_difficulty(user_progress)
    
    if difficulty == "too_easy":
        tips.append("Consider skipping to more advanced lessons or exploring the 'Further Reading' section")
        tips.append("Try the bonus exercises for additional challenge")
    elif difficulty == "too_hard":
        tips.append("Take more time with the examples before moving to exercises")
        tips.append("Review prerequisite lessons if available")
        tips.append("Focus on understanding concepts before memorizing details")
    else:
        tips.append("You're making great progress! Keep up the current pace")
        tips.append("Try explaining concepts in your own words to deepen understanding")
    
    return tips
