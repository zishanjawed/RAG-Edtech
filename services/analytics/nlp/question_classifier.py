"""
Question Type Classifier
Classifies educational questions into categories for analytics.
"""
import re
from typing import Dict, Tuple, List
from shared.logging.logger import get_logger

logger = get_logger("question_classifier")

QUESTION_PATTERNS = {
    "definition": [
        r'\bwhat is\b', r'\bdefine\b', r'\bmeaning of\b',
        r'\bwhat are\b', r'\bwhat does\b', r'\bwhat do\b'
    ],
    "explanation": [
        r'\bhow does\b', r'\bwhy does\b', r'\bexplain\b',
        r'\bhow can\b', r'\bwhy is\b', r'\bwhy are\b',
        r'\bhow do\b', r'\bwhy would\b'
    ],
    "comparison": [
        r'\bdifference between\b', r'\bcompare\b', r'\bversus\b',
        r'\bvs\b', r'\bdiffers from\b', r'\bsimilar to\b',
        r'\bcompared to\b', r'\bcontrast\b'
    ],
    "procedure": [
        r'\bhow to\b', r'\bsteps to\b', r'\bprocess of\b',
        r'\bprocedure for\b', r'\bmethod to\b', r'\bway to\b'
    ],
    "application": [
        r'\bexample of\b', r'\bgive an example\b', r'\bshow\b',
        r'\bdemonstrate\b', r'\bapply\b', r'\buse\b',
        r'\bprovide an example\b', r'\bcan you show\b'
    ],
    "evaluation": [
        r'\bis it true\b', r'\bis it correct\b', r'\bevaluate\b',
        r'\bshould\b', r'\bcould\b', r'\bwould\b',
        r'\bis this\b', r'\bcan\b', r'\bwill\b'
    ]
}


def classify_question(question: str) -> Tuple[str, float]:
    """
    Classify question type using pattern matching.
    
    Args:
        question: The question text to classify
    
    Returns:
        Tuple of (question_type, confidence_score)
        
    Examples:
        >>> classify_question("What is a covalent bond?")
        ('definition', 0.33)
        
        >>> classify_question("How does water form?")
        ('explanation', 0.25)
    """
    if not question or not question.strip():
        return ("general", 0.0)
    
    question_lower = question.lower().strip()
    
    # Calculate scores for each question type
    scores = {}
    for q_type, patterns in QUESTION_PATTERNS.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, question_lower):
                score += 1
        scores[q_type] = score
    
    # If no patterns matched, classify as general
    if not any(scores.values()):
        logger.debug(f"No patterns matched for question: {question[:50]}...")
        return ("general", 0.5)
    
    # Find the best matching type
    best_type = max(scores, key=scores.get)
    max_score = scores[best_type]
    
    # Calculate confidence (normalize by number of patterns for that type)
    confidence = min(max_score / len(QUESTION_PATTERNS[best_type]), 1.0)
    
    logger.debug(
        f"Classified question as '{best_type}' with confidence {confidence:.2f}: "
        f"{question[:50]}..."
    )
    
    return (best_type, round(confidence, 2))


def get_question_types() -> List[str]:
    """
    Get list of all supported question types.
    
    Returns:
        List of question type names
    """
    return list(QUESTION_PATTERNS.keys()) + ["general"]


def get_patterns_for_type(question_type: str) -> List[str]:
    """
    Get regex patterns for a specific question type.
    
    Args:
        question_type: The question type name
    
    Returns:
        List of regex patterns for that type
    """
    return QUESTION_PATTERNS.get(question_type, [])

