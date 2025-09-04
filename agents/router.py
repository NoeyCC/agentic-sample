"""
Router module for intent classification and worker selection.

This module implements the Routing pattern, analyzing user queries to determine
intent and select the appropriate workers to handle the request.
"""
import re
import logging
from typing import List, Dict, Any, Set
from enum import Enum

from core.types import WorkerType, IntentType

logger = logging.getLogger(__name__)

# Define patterns for intent classification
INTENT_PATTERNS = {
    IntentType.RESEARCH: [
        r"(research|find|search|look up|summarize|trends?|market)",
        r"(news|article|blog|report|study|analysis)",
    ],
    IntentType.CODE_ANALYSIS: [
        r"(code|source|implementation|function|class|method)",
        r"(explain|analyze|understand|read|review)",
    ],
    IntentType.DATA_ANALYSIS: [
        r"(data|statistics?|numbers?|figures?|metrics?)",
        r"(analy[sz]e|process|extract|query|report)",
    ],
}

# Map intents to workers
INTENT_TO_WORKERS = {
    IntentType.RESEARCH: [WorkerType.WEB_SEARCH],
    IntentType.CODE_ANALYSIS: [WorkerType.CODE_READ],
    IntentType.DATA_ANALYSIS: [WorkerType.DATA_QUERY],
}

# Default workers to include in all requests
DEFAULT_WORKERS = [WorkerType.WEB_SEARCH]

class Router:
    """
    Routes user queries to appropriate workers based on intent analysis.
    
    Implements the Routing pattern to determine which workers should handle
    a given query based on its content and intent.
    """
    
    def __init__(self):
        """Initialize the router with compiled regex patterns."""
        self.patterns = {
            intent: [re.compile(pattern, re.IGNORECASE) 
                    for pattern in patterns]
            for intent, patterns in INTENT_PATTERNS.items()
        }
    
    def detect_intent(self, query: str) -> List[IntentType]:
        """
        Detect the intent(s) of a user query.
        
        Args:
            query: The user's query string
            
        Returns:
            List of detected intents, ordered by confidence
        """
        query = query.lower()
        matched_intents: Set[IntentType] = set()
        
        for intent, patterns in self.patterns.items():
            if any(pattern.search(query) for pattern in patterns):
                matched_intents.add(intent)
        
        # If no specific intent detected, default to RESEARCH
        if not matched_intents:
            return [IntentType.RESEARCH]
            
        return list(matched_intents)
    
    def select_workers(self, query: str) -> List[WorkerType]:
        """
        Select appropriate workers based on the query.
        
        Args:
            query: The user's query string
            
        Returns:
            List of worker types that should handle this query
        """
        intents = self.detect_intent(query)
        logger.info(f"Detected intents: {[i.value for i in intents]}")
        
        # Get all workers for matched intents
        selected_workers: Set[WorkerType] = set()
        for intent in intents:
            selected_workers.update(INTENT_TO_WORKERS.get(intent, []))
        
        # Add default workers if no specific workers were selected
        if not selected_workers:
            selected_workers.update(DEFAULT_WORKERS)
        
        # Convert to list for deterministic ordering
        return list(selected_workers)
    
    def create_execution_plan(self, query: str) -> Dict[str, Any]:
        """
        Create an execution plan for the query.
        
        Args:
            query: The user's query string
            
        Returns:
            Dictionary containing the execution plan
        """
        workers = self.select_workers(query)
        
        return {
            "query": query,
            "required_workers": workers,
            "context": {
                "intents": [intent.value for intent in self.detect_intent(query)],
                "source": "router"
            }
        }
