"""
Tests for question classifier.
"""
import pytest
import sys
import os

# Add services to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from services.analytics.nlp.question_classifier import (
    classify_question,
    get_question_types,
    get_patterns_for_type
)


class TestQuestionClassifier:
    """Test question classification."""
    
    def test_definition_questions(self):
        """Test definition type classification."""
        questions = [
            "What is a covalent bond?",
            "Define molecular structure",
            "What are double bonds?",
            "What does electronegativity mean?"
        ]
        for q in questions:
            q_type, confidence = classify_question(q)
            assert q_type == "definition", f"Failed for: {q}"
            assert confidence > 0, f"Zero confidence for: {q}"
    
    def test_explanation_questions(self):
        """Test explanation type classification."""
        questions = [
            "How does water form?",
            "Why does ice float?",
            "Explain the bonding process",
            "How can atoms bond?",
            "Why are noble gases stable?"
        ]
        for q in questions:
            q_type, confidence = classify_question(q)
            assert q_type == "explanation", f"Failed for: {q}"
            assert confidence > 0, f"Zero confidence for: {q}"
    
    def test_comparison_questions(self):
        """Test comparison type classification."""
        questions = [
            "What is the difference between ionic and covalent bonds?",
            "Compare single and double bonds",
            "How do metals differ from nonmetals?",
            "What's similar to ionic bonding?",
            "Contrast acids and bases"
        ]
        for q in questions:
            q_type, confidence = classify_question(q)
            assert q_type == "comparison", f"Failed for: {q}"
            assert confidence > 0, f"Zero confidence for: {q}"
    
    def test_procedure_questions(self):
        """Test procedure type classification."""
        questions = [
            "How to draw Lewis structures?",
            "What are the steps to balance equations?",
            "Explain the process of crystallization",
            "What's the procedure for titration?",
            "How to calculate molarity?"
        ]
        for q in questions:
            q_type, confidence = classify_question(q)
            assert q_type == "procedure", f"Failed for: {q}"
            assert confidence > 0, f"Zero confidence for: {q}"
    
    def test_application_questions(self):
        """Test application type classification."""
        questions = [
            "Give an example of a covalent compound",
            "Show me how to apply this concept",
            "Demonstrate bonding with water",
            "Provide an example of redox reactions",
            "Can you show oxidation states?"
        ]
        for q in questions:
            q_type, confidence = classify_question(q)
            assert q_type == "application", f"Failed for: {q}"
            assert confidence > 0, f"Zero confidence for: {q}"
    
    def test_evaluation_questions(self):
        """Test evaluation type classification."""
        questions = [
            "Is it true that water is polar?",
            "Is this correct?",
            "Should I use this method?",
            "Could this be a valid structure?",
            "Would this reaction occur?"
        ]
        for q in questions:
            q_type, confidence = classify_question(q)
            assert q_type == "evaluation", f"Failed for: {q}"
            assert confidence > 0, f"Zero confidence for: {q}"
    
    def test_general_questions(self):
        """Test general type for unclassified questions."""
        questions = [
            "Tell me about chemistry",
            "I need help",
            "Chemistry please"
        ]
        for q in questions:
            q_type, confidence = classify_question(q)
            assert q_type == "general", f"Failed for: {q}"
    
    def test_empty_question(self):
        """Test empty question handling."""
        q_type, confidence = classify_question("")
        assert q_type == "general"
        assert confidence == 0.0
    
    def test_none_question(self):
        """Test None question handling."""
        q_type, confidence = classify_question(None)
        assert q_type == "general"
        assert confidence == 0.0
    
    def test_confidence_values(self):
        """Test confidence scores are valid."""
        questions = [
            "What is a bond?",
            "How does water form?",
            "Compare ionic and covalent"
        ]
        for q in questions:
            q_type, confidence = classify_question(q)
            assert 0.0 <= confidence <= 1.0, f"Invalid confidence {confidence} for: {q}"
            assert isinstance(confidence, float), f"Confidence not float for: {q}"
    
    def test_get_question_types(self):
        """Test getting list of question types."""
        types = get_question_types()
        assert len(types) == 7  # 6 types + general
        assert "definition" in types
        assert "explanation" in types
        assert "comparison" in types
        assert "procedure" in types
        assert "application" in types
        assert "evaluation" in types
        assert "general" in types
    
    def test_get_patterns_for_type(self):
        """Test getting patterns for specific types."""
        definition_patterns = get_patterns_for_type("definition")
        assert len(definition_patterns) > 0
        assert any("what is" in p for p in definition_patterns)
        
        unknown_patterns = get_patterns_for_type("unknown")
        assert len(unknown_patterns) == 0
    
    def test_case_insensitive(self):
        """Test classification is case-insensitive."""
        questions = [
            ("What is a bond?", "WHAT IS A BOND?"),
            ("How does it work?", "HOW DOES IT WORK?"),
            ("Compare these", "COMPARE THESE")
        ]
        for q1, q2 in questions:
            type1, _ = classify_question(q1)
            type2, _ = classify_question(q2)
            assert type1 == type2, f"Case sensitivity issue: {q1} vs {q2}"
    
    def test_multiple_patterns_match(self):
        """Test questions matching multiple patterns."""
        # This question could match both definition and explanation
        q = "What is the reason this occurs?"
        q_type, confidence = classify_question(q)
        # Should classify as something (not fail)
        assert q_type in get_question_types()
    
    def test_chemistry_specific_questions(self):
        """Test with chemistry-specific educational questions."""
        chemistry_questions = {
            "What is electronegativity in chemistry?": "definition",
            "How does hybridization work?": "explanation",
            "What's the difference between sp2 and sp3 hybridization?": "comparison",
            "How to determine oxidation states?": "procedure",
            "Give an example of a redox reaction": "application",
            "Is this Lewis structure correct?": "evaluation"
        }
        
        for question, expected_type in chemistry_questions.items():
            q_type, confidence = classify_question(question)
            assert q_type == expected_type, f"Expected {expected_type} but got {q_type} for: {question}"
            assert confidence > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

