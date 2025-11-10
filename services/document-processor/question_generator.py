"""
LLM-powered question generator for documents.
Generates 5 suggested questions per document using GPT-4.
"""
from openai import AsyncOpenAI
import json
from typing import List, Dict, Optional
from shared.logging.logger import get_logger
from config import settings

logger = get_logger("question_generator", settings.log_level)

# Lazy-initialize OpenAI client
_openai_client: Optional[AsyncOpenAI] = None

def get_openai_client() -> AsyncOpenAI:
    """Get or create OpenAI client."""
    global _openai_client
    if _openai_client is None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set")
        _openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _openai_client


QUESTION_GENERATION_PROMPT = """You are an educational AI assistant specialized in creating study questions. Given information about an educational document, generate 5 specific, actionable questions that a student would likely ask.

CRITICAL REQUIREMENTS:
- Questions MUST be based ONLY on the content preview provided
- DO NOT generate generic questions like "Create a study plan", "What should I study?", or "How to prepare for exam?"
- Focus on specific concepts, definitions, formulas, and processes mentioned in the preview
- Each question should target retrievable information from THIS document
- Questions should be answerable using the document content

Make questions:
- Directly related to specific content in the preview
- Progressively complex (from basic understanding to advanced application)
- Varied in type to cover different learning objectives
- Clear and concise
- Content-specific, not generic study advice

Document Information:
Title: {title}
Subject: {subject}
Tags: {tags}
Content Preview (first 500 characters):
{content_preview}

Generate exactly 5 questions about the ACTUAL CONTENT of this document. Return ONLY a valid JSON array with this exact format:
[
  {{"question": "What is [specific concept from preview]?", "category": "definition", "difficulty": "easy"}},
  {{"question": "Explain how [specific process from preview] works", "category": "explanation", "difficulty": "medium"}},
  {{"question": "Compare [concept A] with [concept B]", "category": "comparison", "difficulty": "medium"}},
  {{"question": "Calculate/Solve [specific formula/problem type]", "category": "procedure", "difficulty": "hard"}},
  {{"question": "Apply [specific concept] to [scenario]", "category": "application", "difficulty": "hard"}}
]

Valid categories: definition, explanation, comparison, procedure, application
Valid difficulty levels: easy, medium, hard

EXAMPLES OF GOOD QUESTIONS (content-specific):
- "What is the formula for calculating F1 Score?"
- "Explain how gradient descent optimizes neural networks"
- "Compare ReLU and Sigmoid activation functions"

EXAMPLES OF BAD QUESTIONS (generic):
- "Create a study plan"
- "What should I focus on?"
- "How do I prepare for the exam?"
"""


async def generate_questions_for_document(
    content_id: str,
    title: str,
    subject: str,
    content_preview: str,
    tags: List[str] = None
) -> List[Dict]:
    """
    Generate 5 suggested questions for a document using GPT-4.
    
    Args:
        content_id: Document ID
        title: Document title
        subject: Document subject
        content_preview: First ~500 chars of document
        tags: Optional tags
    
    Returns:
        List of question dictionaries with id, question, category, difficulty
    """
    try:
        logger.info(f"Generating questions for document {content_id} ({subject})")
        
        # Format tags for prompt
        tags_str = ", ".join(tags) if tags else "None"
        
        # Create prompt
        prompt = QUESTION_GENERATION_PROMPT.format(
            title=title,
            subject=subject,
            tags=tags_str,
            content_preview=content_preview[:500]
        )
        
        # Call GPT-4o-mini (cost-effective for question generation)
        client = get_openai_client()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert educational content analyzer who creates perfect study questions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=600,
            response_format={"type": "json_object"}  # Enforce JSON output (Nov 2025 feature)
        )
        
        # Parse response
        result = response.choices[0].message.content
        logger.debug(f"GPT-4 response: {result}")
        
        # Handle both array and object responses
        parsed = json.loads(result)
        if isinstance(parsed, dict) and 'questions' in parsed:
            questions_list = parsed['questions']
        elif isinstance(parsed, list):
            questions_list = parsed
        else:
            raise ValueError(f"Unexpected response format: {parsed}")
        
        # Validate and add IDs
        validated_questions = []
        for i, q in enumerate(questions_list[:5]):  # Take first 5
            validated_questions.append({
                "id": f"{content_id}-q{i+1}",
                "question": q.get("question", ""),
                "category": q.get("category", "explanation"),
                "difficulty": q.get("difficulty", "medium"),
                "content_id": content_id
            })
        
        logger.info(f"Generated {len(validated_questions)} questions for {content_id}")
        return validated_questions
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from GPT-4: {e}")
        return get_fallback_questions(content_id, subject, tags)
    except Exception as e:
        logger.error(f"Failed to generate questions: {e}")
        # Return fallback generic questions
        return get_fallback_questions(content_id, subject, tags)


def get_fallback_questions(content_id: str, subject: str, tags: List[str] = None) -> List[Dict]:
    """
    Fallback questions if LLM generation fails.
    Returns subject-specific generic questions.
    """
    logger.warning(f"Using fallback questions for {content_id}")
    
    # Subject-specific question templates
    subject_templates = {
        "Chemistry": [
            {"question": "What are the molecular structures and bonding types discussed?", "category": "definition", "difficulty": "easy"},
            {"question": "Explain the chemical reaction mechanisms in this document.", "category": "explanation", "difficulty": "medium"},
            {"question": "Compare different compounds and their properties.", "category": "comparison", "difficulty": "medium"},
            {"question": "What are the calculation procedures for molar mass and concentration?", "category": "procedure", "difficulty": "hard"},
            {"question": "How do these chemical principles apply to real experiments?", "category": "application", "difficulty": "hard"}
        ],
        "Physics": [
            {"question": "Define the key physics terms and laws in this document.", "category": "definition", "difficulty": "easy"},
            {"question": "Explain the equations and their derivations.", "category": "explanation", "difficulty": "medium"},
            {"question": "Compare different force models or energy types.", "category": "comparison", "difficulty": "medium"},
            {"question": "What are the steps to solve kinematics problems?", "category": "procedure", "difficulty": "hard"},
            {"question": "Apply these physics principles to motion analysis.", "category": "application", "difficulty": "hard"}
        ],
        "Biology": [
            {"question": "What are the cell structures and organelles described?", "category": "definition", "difficulty": "easy"},
            {"question": "Explain the biological processes and mechanisms covered.", "category": "explanation", "difficulty": "medium"},
            {"question": "Compare different biological systems and their functions.", "category": "comparison", "difficulty": "medium"},
            {"question": "Describe the experimental procedures and methodologies.", "category": "procedure", "difficulty": "hard"},
            {"question": "How do these biological concepts apply to human health?", "category": "application", "difficulty": "hard"}
        ],
        "Mathematics": [
            {"question": "What are the key mathematical definitions and theorems covered?", "category": "definition", "difficulty": "easy"},
            {"question": "Explain the mathematical proofs and derivations.", "category": "explanation", "difficulty": "medium"},
            {"question": "Compare different solution approaches or methods.", "category": "comparison", "difficulty": "medium"},
            {"question": "What are the steps to solve these equation types?", "category": "procedure", "difficulty": "hard"},
            {"question": "Apply these mathematical concepts to word problems.", "category": "application", "difficulty": "hard"}
        ],
        "Machine Learning": [
            {"question": "What are the key algorithms and techniques covered?", "category": "definition", "difficulty": "easy"},
            {"question": "Explain how neural network architectures work.", "category": "explanation", "difficulty": "medium"},
            {"question": "Compare supervised and unsupervised learning approaches.", "category": "comparison", "difficulty": "medium"},
            {"question": "What are the formulas for model evaluation metrics?", "category": "procedure", "difficulty": "hard"},
            {"question": "How do these ML concepts apply to specific problems?", "category": "application", "difficulty": "hard"}
        ],
        "Deep Learning": [
            {"question": "Define the neural network components and layers.", "category": "definition", "difficulty": "easy"},
            {"question": "Explain the backpropagation algorithm.", "category": "explanation", "difficulty": "medium"},
            {"question": "Compare different optimization techniques.", "category": "comparison", "difficulty": "medium"},
            {"question": "What are the training procedures for CNNs?", "category": "procedure", "difficulty": "hard"},
            {"question": "Apply regularization techniques to prevent overfitting.", "category": "application", "difficulty": "hard"}
        ]
    }
    
    # Use subject-specific or generic questions
    templates = subject_templates.get(subject, [
        {"question": f"What are the main concepts in this {subject} document?", "category": "definition", "difficulty": "easy"},
        {"question": f"Explain the key topics covered in detail.", "category": "explanation", "difficulty": "medium"},
        {"question": f"How do these concepts relate to each other?", "category": "comparison", "difficulty": "medium"},
        {"question": f"What are the practical applications of these concepts?", "category": "application", "difficulty": "hard"},
        {"question": f"What should I focus on for exam preparation?", "category": "evaluation", "difficulty": "medium"}
    ])
    
    return [
        {
            "id": f"{content_id}-q{i+1}",
            "question": q["question"],
            "category": q["category"],
            "difficulty": q["difficulty"],
            "content_id": content_id
        }
        for i, q in enumerate(templates[:5])
    ]


async def generate_global_questions(user_id: str, documents: List[Dict]) -> List[Dict]:
    """
    Generate cross-document questions for global chat.
    Analyzes user's entire document collection.
    
    Args:
        user_id: User ID
        documents: List of document metadata dicts
    
    Returns:
        List of 5 global questions
    """
    try:
        logger.info(f"Generating global questions for user {user_id} ({len(documents)} docs)")
        
        # Extract subjects and topics
        subjects = list(set(doc.get('metadata', {}).get('subject', 'General') for doc in documents))
        all_tags = []
        for doc in documents:
            all_tags.extend(doc.get('tags', []))
        unique_tags = list(set(all_tags))[:10]  # Top 10 most common tags
        
        # Create prompt for global questions
        prompt = f"""You are an educational AI assistant. A student has {len(documents)} documents covering these subjects: {', '.join(subjects[:5])}.

Common topics/tags: {', '.join(unique_tags) if unique_tags else 'various topics'}

Generate 5 questions that help the student understand and synthesize the CONTENT across documents:
- Compare specific concepts, formulas, or theories from these subject areas
- Ask about relationships between technical topics
- Focus on definitions, procedures, and applications covered in the materials
- Enable synthesis of information across multiple sources

STRICT REQUIREMENTS:
- Questions must reference ACTUAL CONTENT that would exist in these subject documents
- NO generic questions like "Create a study plan", "What should I study?", "How to prepare?"
- NO meta-level questions about organization or learning strategies
- Focus on RETRIEVABLE INFORMATION from document content

GOOD EXAMPLES:
- "Compare the optimization techniques in machine learning"
- "What are the mathematical formulas for neural network training?"
- "Explain the relationship between activation functions and gradient flow"
- "How do regularization methods prevent overfitting?"

BAD EXAMPLES:
- "Create a study plan"
- "What topics am I missing?"
- "How should I organize my study time?"

Return ONLY a valid JSON array:
[
  {{"question": "Compare [specific concept A] with [specific concept B]", "category": "comparison", "difficulty": "medium"}},
  ...
]

Valid categories: definition, explanation, comparison, procedure, application"""
        
        client = get_openai_client()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert educational content synthesizer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        result = response.choices[0].message.content
        parsed = json.loads(result)
        questions_list = parsed if isinstance(parsed, list) else parsed.get('questions', [])
        
        validated_questions = []
        for i, q in enumerate(questions_list[:5]):
            validated_questions.append({
                "id": f"global-{user_id}-q{i+1}",
                "question": q.get("question", ""),
                "category": q.get("category", "comparison"),
                "difficulty": q.get("difficulty", "medium"),
                "user_id": user_id,
                "is_global": True
            })
        
        logger.info(f"Generated {len(validated_questions)} global questions")
        return validated_questions
        
    except Exception as e:
        logger.error(f"Failed to generate global questions: {e}")
        return get_fallback_global_questions(user_id, subjects if subjects else ["General"])


def get_fallback_global_questions(user_id: str, subjects: List[str]) -> List[Dict]:
    """Content-based fallback global questions."""
    subject_str = subjects[0] if subjects else "the subject"
    
    templates = [
        {"question": f"Compare the key theories and models across my {subject_str} documents.", "category": "comparison"},
        {"question": f"What are the fundamental formulas and equations covered?", "category": "definition"},
        {"question": f"Explain the relationships between different concepts in my materials.", "category": "explanation"},
        {"question": f"How do the experimental procedures differ across documents?", "category": "comparison"},
        {"question": f"What practical applications are discussed in my documents?", "category": "application"}
    ]
    
    return [
        {
            "id": f"global-{user_id}-q{i+1}",
            "question": q["question"],
            "category": q["category"],
            "difficulty": "medium",
            "user_id": user_id,
            "is_global": True
        }
        for i, q in enumerate(templates)
    ]

