"""
Text summarization tool.

This module provides functionality for generating concise summaries from text content.
It includes both a simple extractive summarizer and a placeholder for more advanced
abstractive summarization.
"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

# Download required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

@dataclass
class SummaryConfig:
    """Configuration for text summarization."""
    max_sentences: int = 5
    min_sentence_length: int = 10
    language: str = "english"
    use_stopwords: bool = True
    summary_ratio: float = 0.2  # Target ratio of summary to original text

class Summarizer:
    """
    Text summarization utility.
    
    Provides both extractive and abstractive summarization capabilities.
    The extractive method is implemented, while abstractive is a placeholder
    that would typically use a language model.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the summarizer.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = self._parse_config(config or {})
        self.stop_words = set(stopwords.words(self.config.language)) if self.config.use_stopwords else set()
    
    def _parse_config(self, config: Dict[str, Any]) -> SummaryConfig:
        """
        Parse and validate the summarizer configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            SummaryConfig instance
        """
        return SummaryConfig(
            max_sentences=config.get("max_sentences", 5),
            min_sentence_length=config.get("min_sentence_length", 10),
            language=config.get("language", "english"),
            use_stopwords=config.get("use_stopwords", True),
            summary_ratio=min(max(config.get("summary_ratio", 0.2), 0.01), 1.0)
        )
    
    def summarize(self, text: str, method: str = "extractive") -> str:
        """
        Generate a summary of the input text.
        
        Args:
            text: The text to summarize
            method: The summarization method to use ('extractive' or 'abstractive')
            
        Returns:
            The generated summary
        """
        if not text.strip():
            return ""
            
        if method.lower() == "extractive":
            return self._extractive_summarize(text)
        elif method.lower() == "abstractive":
            return self._abstractive_summarize(text)
        else:
            raise ValueError(f"Unsupported summarization method: {method}")
    
    def _extractive_summarize(self, text: str) -> str:
        """
        Generate an extractive summary of the input text.
        
        This method selects the most important sentences from the original text
        based on word frequency and sentence position.
        
        Args:
            text: The text to summarize
            
        Returns:
            The generated summary
        """
        # Tokenize the text into sentences
        sentences = sent_tokenize(text, language=self.config.language)
        
        # Filter out very short sentences
        sentences = [s for s in sentences if len(s.split()) >= self.config.min_sentence_length]
        
        if not sentences:
            return ""
            
        # If the text is already short enough, return it as is
        if len(sentences) <= self.config.max_sentences:
            return " ".join(sentences)
        
        # Calculate word frequencies
        word_frequencies = self._calculate_word_frequencies(text)
        
        # Score sentences based on word frequencies and position
        sentence_scores = self._score_sentences(sentences, word_frequencies)
        
        # Get top N sentences
        top_sentences = sorted(
            sentence_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:self.config.max_sentences]
        
        # Sort the selected sentences by their original position
        top_sentences_sorted = sorted(top_sentences, key=lambda x: x[0])
        
        # Join the selected sentences to form the summary
        summary = " ".join([sentences[idx] for idx, _ in top_sentences_sorted])
        
        return summary
    
    def _calculate_word_frequencies(self, text: str) -> Dict[str, int]:
        """
        Calculate word frequencies in the given text.
        
        Args:
            text: The input text
            
        Returns:
            Dictionary mapping words to their frequencies
        """
        # Tokenize into words and remove punctuation
        words = word_tokenize(text.lower(), language=self.config.language)
        words = [word for word in words if word.isalnum()]
        
        # Remove stopwords
        if self.config.use_stopwords:
            words = [word for word in words if word not in self.stop_words]
        
        # Calculate frequencies
        word_frequencies = defaultdict(int)
        for word in words:
            word_frequencies[word] += 1
            
        # Normalize frequencies
        if word_frequencies:
            max_freq = max(word_frequencies.values())
            for word in word_frequencies:
                word_frequencies[word] = word_frequencies[word] / max_freq
                
        return dict(word_frequencies)
    
    def _score_sentences(
        self,
        sentences: List[str],
        word_frequencies: Dict[str, float]
    ) -> Dict[int, float]:
        """
        Score sentences based on word frequencies and position.
        
        Args:
            sentences: List of sentences
            word_frequencies: Dictionary of word frequencies
            
        Returns:
            Dictionary mapping sentence indices to their scores
        """
        sentence_scores = {}
        
        for idx, sentence in enumerate(sentences):
            words = word_tokenize(sentence.lower())
            words = [word for word in words if word.isalnum()]
            
            # Calculate sentence score based on word frequencies
            score = 0.0
            for word in words:
                if word in word_frequencies:
                    score += word_frequencies[word]
            
            # Normalize by sentence length
            if len(words) > 0:
                score /= len(words)
            
            # Boost score for sentences at the beginning or end of the text
            position = idx / len(sentences)
            if position < 0.1 or position > 0.9:  # First or last 10%
                score *= 1.5
            
            sentence_scores[idx] = score
            
        return sentence_scores
    
    def _abstractive_summarize(self, text: str) -> str:
        """
        Generate an abstractive summary of the input text.
        
        This is a placeholder that would typically use a language model.
        In a real implementation, this would use something like T5, BART, or GPT.
        
        Args:
            text: The text to summarize
            
        Returns:
            The generated summary
        """
        # In a real implementation, this would use a pre-trained model
        # For now, we'll fall back to extractive summarization
        # with a note that this is a placeholder
        return (
            "[Abstractive Summarization Placeholder - Using Extractive Instead]\n\n" +
            self._extractive_summarize(text) +
            "\n\nNote: Abstractive summarization would be implemented with a language model in a production system."
        )

# Example usage
if __name__ == "__main__":
    # Example text to summarize
    sample_text = """
    Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to natural 
    intelligence displayed by animals including humans. AI research has been defined as the field 
    of study of intelligent agents, which refers to any system that perceives its environment and 
    takes actions that maximize its chance of achieving its goals.
    
    The traditional problems (or goals) of AI research include reasoning, knowledge representation, 
    planning, learning, natural language processing, perception, and the ability to move and 
    manipulate objects. General intelligence (the ability to solve an arbitrary problem) is among 
    the field's long-term goals.
    
    The field was founded on the assumption that human intelligence "can be so precisely described 
    that a machine can be made to simulate it". This raised philosophical arguments about the mind 
    and the ethical consequences of creating artificial beings endowed with human-like intelligence.
    """
    
    # Create a summarizer
    summarizer = Summarizer({
        "max_sentences": 3,
        "min_sentence_length": 5,
        "language": "english"
    })
    
    # Generate and print the summary
    summary = summarizer.summarize(sample_text, method="extractive")
    print("=== Original Text ===\n")
    print(sample_text)
    print("\n=== Extractive Summary ===\n")
    print(summary)
    
    # Try abstractive summarization (will fall back to extractive with a note)
    print("\n=== Abstractive Summary (Placeholder) ===\n")
    abstractive_summary = summarizer.summarize(sample_text, method="abstractive")
    print(abstractive_summary)
