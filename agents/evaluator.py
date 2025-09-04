"""
Evaluator component for assessing the quality of generated briefs.

This module implements the Evaluator class which is responsible for evaluating
the quality, completeness, and relevance of generated briefs against the original query.
"""
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

from core.types import EvaluationResult, BriefOutput
from tools.summarizer import Summarizer

logger = logging.getLogger(__name__)

@dataclass
class EvaluationCriteria:
    """Criteria for evaluating brief quality."""
    min_length: int = 100
    max_length: int = 2000
    required_sections: List[str] = None
    min_references: int = 1
    max_references: int = 10
    min_coverage: float = 0.7  # Minimum coverage of query terms
    max_avg_sentence_length: int = 25
    max_readability_score: float = 14.0  # Flesch-Kincaid grade level

class Evaluator:
    """
    Evaluates the quality and completeness of generated briefs.
    
    Implements the Evaluator-Optimizer pattern to assess briefs against
    various quality criteria and provide feedback for improvement.
    """
    
    def __init__(self, criteria: Optional[Dict[str, Any]] = None):
        """
        Initialize the Evaluator.
        
        Args:
            criteria: Optional dictionary of criteria overrides
        """
        self.criteria = self._parse_criteria(criteria or {})
        self.summarizer = Summarizer()
    
    def _parse_criteria(self, criteria: Dict[str, Any]) -> EvaluationCriteria:
        """
        Parse and validate evaluation criteria.
        
        Args:
            criteria: Dictionary of criteria overrides
            
        Returns:
            EvaluationCriteria instance
        """
        return EvaluationCriteria(
            min_length=criteria.get("min_length", 100),
            max_length=criteria.get("max_length", 2000),
            required_sections=criteria.get("required_sections", 
                ["introduction", "key_points", "conclusion"]),
            min_references=criteria.get("min_references", 1),
            max_references=criteria.get("max_references", 10),
            min_coverage=criteria.get("min_coverage", 0.7),
            max_avg_sentence_length=criteria.get("max_avg_sentence_length", 25),
            max_readability_score=criteria.get("max_readability_score", 14.0)
        )
    
    def evaluate_brief(
        self,
        brief: BriefOutput,
        original_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> EvaluationResult:
        """
        Evaluate the quality of a generated brief.
        
        Args:
            brief: The generated brief to evaluate
            original_query: The original user query
            context: Optional context dictionary
            
        Returns:
            EvaluationResult with score and feedback
        """
        if not brief or not brief.content:
            return EvaluationResult(
                is_complete=False,
                feedback="Brief is empty or invalid",
                score=0.0
            )
        
        # Initialize feedback and score components
        feedback = []
        score_components = {}
        
        # 1. Check brief length
        content_length = len(brief.content)
        if content_length < self.criteria.min_length:
            feedback.append(f"Brief is too short ({content_length} chars, minimum {self.criteria.min_length} required).")
            score_components["length"] = 0.0
        elif content_length > self.criteria.max_length:
            feedback.append(f"Brief is too long ({content_length} chars, maximum {self.criteria.max_length} allowed).")
            score_components["length"] = 0.5
        else:
            score_components["length"] = 1.0
        
        # 2. Check for required sections
        missing_sections = []
        content_lower = brief.content.lower()
        for section in self.criteria.required_sections:
            if section.lower() not in content_lower:
                missing_sections.append(section)
        
        if missing_sections:
            feedback.append(f"Missing required sections: {', '.join(missing_sections)}")
            score_components["sections"] = 0.5 if len(missing_sections) < len(self.criteria.required_sections) else 0.0
        else:
            score_components["sections"] = 1.0
        
        # 3. Check references
        num_references = len(brief.references) if brief.references else 0
        if num_references < self.criteria.min_references:
            feedback.append(f"Insufficient references ({num_references}, minimum {self.criteria.min_references} required).")
            score_components["references"] = 0.0
        elif num_references > self.criteria.max_references:
            feedback.append(f"Too many references ({num_references}, maximum {self.criteria.max_references} allowed).")
            score_components["references"] = 0.5
        else:
            score_components["references"] = 1.0
        
        # 4. Check query term coverage
        query_terms = set(term.lower() for term in re.findall(r'\b\w+\b', original_query))
        if query_terms:
            covered_terms = sum(1 for term in query_terms if term in content_lower)
            coverage = covered_terms / len(query_terms)
            if coverage < self.criteria.min_coverage:
                feedback.append(f"Low query term coverage ({coverage:.1%}, minimum {self.criteria.min_coverage:.0%} required).")
                score_components["coverage"] = coverage / self.criteria.min_coverage  # Normalized score
            else:
                score_components["coverage"] = 1.0
        
        # 5. Check readability (simplified)
        sentences = [s for s in re.split(r'[.!?]', brief.content) if s.strip()]
        if sentences:
            words = [word for sent in sentences for word in sent.split()]
            avg_sentence_length = len(words) / len(sentences) if sentences else 0
            if avg_sentence_length > self.criteria.max_avg_sentence_length:
                feedback.append(f"Average sentence length is too high ({avg_sentence_length:.1f} words, maximum {self.criteria.max_avg_sentence_length} recommended).")
                score_components["readability"] = 0.5
            else:
                score_components["readability"] = 1.0
        
        # Calculate overall score (weighted average)
        weights = {
            "length": 0.2,
            "sections": 0.3,
            "references": 0.2,
            "coverage": 0.2,
            "readability": 0.1
        }
        
        # Calculate weighted score
        total_weight = sum(weights.get(k, 0) for k in score_components)
        if total_weight > 0:
            weighted_score = sum(
                score * weights.get(metric, 0)
                for metric, score in score_components.items()
            ) / total_weight
        else:
            weighted_score = 0.0
        
        # Determine if brief is complete
        is_complete = all(
            score_components.get(metric, 0) >= 0.7
            for metric in ["length", "sections", "references", "coverage"]
        )
        
        # Prepare feedback
        if not feedback:
            feedback.append("Brief meets all quality criteria.")
        
        # Add score breakdown to feedback
        feedback.append("\nScore Breakdown:" + "".join(
            f"\n- {metric}: {score:.1f}"
            for metric, score in sorted(score_components.items())
        ))
        
        return EvaluationResult(
            is_complete=is_complete,
            feedback="\n".join(feedback),
            score=weighted_score
        )
    
    def generate_improvement_suggestions(
        self,
        evaluation: EvaluationResult,
        brief: BriefOutput,
        original_query: str
    ) -> List[str]:
        """
        Generate specific suggestions for improving the brief.
        
        Args:
            evaluation: The evaluation result
            brief: The original brief
            original_query: The original user query
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        # Check brief length
        content_length = len(brief.content)
        if content_length < self.criteria.min_length:
            suggestions.append(
                f"Expand the brief by adding more details or examples. "
                f"Aim for at least {self.criteria.min_length} characters."
            )
        elif content_length > self.criteria.max_length:
            suggestions.append(
                f"Consider making the brief more concise. "
                f"Try to stay under {self.criteria.max_length} characters."
            )
        
        # Check for missing sections
        content_lower = brief.content.lower()
        missing_sections = [
            section for section in self.criteria.required_sections
            if section.lower() not in content_lower
        ]
        
        for section in missing_sections:
            suggestions.append(
                f"Add a '{section}' section to improve the structure of the brief."
            )
        
        # Check references
        num_references = len(brief.references) if brief.references else 0
        if num_references < self.criteria.min_references:
            suggestions.append(
                f"Add more references to support your claims. "
                f"Aim for at least {self.criteria.min_references} references."
            )
        
        # Check query coverage
        query_terms = set(term.lower() for term in re.findall(r'\b\w+\b', original_query) if len(term) > 3)
        if query_terms:
            content_terms = set(re.findall(r'\b\w+\b', brief.content.lower()))
            missing_terms = [term for term in query_terms if term not in content_terms]
            
            if missing_terms and len(missing_terms) < 5:  # Only suggest if a few terms are missing
                suggestions.append(
                    f"Consider addressing these key terms from the query: "
                    f"{', '.join(missing_terms)}."
                )
        
        # Check readability
        sentences = [s for s in re.split(r'[.!?]', brief.content) if s.strip()]
        if sentences:
            words = [word for sent in sentences for word in sent.split()]
            avg_sentence_length = len(words) / len(sentences) if sentences else 0
            
            if avg_sentence_length > self.criteria.max_avg_sentence_length:
                suggestions.append(
                    "Break down long sentences into shorter ones to improve readability. "
                    f"Aim for an average of {self.criteria.max_avg_sentence_length} words per sentence."
                )
        
        # If no specific suggestions, provide general ones
        if not suggestions:
            suggestions.extend([
                "The brief is well-structured. Consider adding more specific examples or case studies.",
                "Review the brief for any technical jargon that might not be familiar to all readers.",
                "Consider adding visual elements like bullet points or numbered lists to improve scannability."
            ])
        
        return suggestions

# Example usage
if __name__ == "__main__":
    # Example brief
    example_brief = BriefOutput(
        title="Sample Brief",
        content="""
        Introduction:
        This is a sample brief about artificial intelligence.
        
        Key Points:
        - AI is transforming industries
        - Machine learning is a subset of AI
        - Deep learning enables complex pattern recognition
        
        Conclusion:
        AI has significant potential across various domains.
        """,
        references=[
            {"title": "AI Research Paper", "url": "https://example.com/ai-paper"},
            {"title": "ML Overview", "url": "https://example.com/ml-overview"}
        ],
        generated_at=datetime.now().isoformat()
    )
    
    # Create an evaluator with default criteria
    evaluator = Evaluator()
    
    # Example query
    query = "What are the latest trends in artificial intelligence?"
    
    # Evaluate the brief
    result = evaluator.evaluate_brief(example_brief, query)
    
    # Print results
    print(f"Evaluation Score: {result.score:.1%}")
    print(f"Is Complete: {result.is_complete}")
    print("\nFeedback:")
    print(result.feedback)
    
    # Get improvement suggestions
    print("\nImprovement Suggestions:")
    for i, suggestion in enumerate(evaluator.generate_improvement_suggestions(
        result, example_brief, query
    ), 1):
        print(f"{i}. {suggestion}")
