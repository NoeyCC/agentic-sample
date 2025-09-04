"""
Web Search Tool with stub implementation for offline use.

This module provides a web search interface that can be used by workers
to perform web searches. It includes a stub implementation for offline use.
"""
import os
import json
import random
from typing import List, Dict, Optional, Any
import httpx
from datetime import datetime

from core.types import WebSearchResult

class WebSearchTool:
    """
    A tool for performing web searches with both online and offline capabilities.
    
    In online mode, it uses a real search API (DuckDuckGo).
    In offline mode, it returns mock search results.
    """
    
    def __init__(self, offline: bool = True, api_key: Optional[str] = None):
        """
        Initialize the WebSearchTool.
        
        Args:
            offline: If True, use the stub implementation
            api_key: API key for the search service (not used in stub)
        """
        self.offline = offline
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Mock data for offline mode
        self.mock_data = [
            {
                "title": "Example Search Result 1",
                "url": "https://example.com/1",
                "snippet": "This is a sample search result for testing purposes.",
                "source": "mock"
            },
            {
                "title": "Example Search Result 2",
                "url": "https://example.com/2",
                "snippet": "Another sample search result with different content.",
                "source": "mock"
            },
            {
                "title": "Example Search Result 3",
                "url": "https://example.com/3",
                "snippet": "Yet another example result with unique information.",
                "source": "mock"
            }
        ]
    
    async def search(self, query: str, num_results: int = 3) -> List[WebSearchResult]:
        """
        Perform a web search.
        
        Args:
            query: The search query string
            num_results: Maximum number of results to return
            
        Returns:
            List of search results
        """
        if self.offline:
            return self._mock_search(query, num_results)
        
        try:
            return await self._real_search(query, num_results)
        except Exception as e:
            print(f"Error performing web search: {e}")
            print("Falling back to mock search")
            return self._mock_search(query, num_results)
    
    async def _real_search(self, query: str, num_results: int) -> List[WebSearchResult]:
        """
        Perform a real web search using DuckDuckGo API.
        
        Args:
            query: The search query string
            num_results: Maximum number of results to return
            
        Returns:
            List of search results
        """
        # This is a placeholder for a real search API implementation
        # In a real implementation, you would use an actual search API here
        # For example, using DuckDuckGo's API or another search service
        
        # Example implementation (commented out as it requires an actual API key)
        """
        params = {
            'q': query,
            'format': 'json',
            'no_html': 1,
            'no_redirect': 1,
            'skip_disambig': 1,
            't': 'agentic_sample_app'
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
            
        response = await self.client.get(
            'https://api.duckduckgo.com/',
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"Search API returned {response.status_code}")
            
        data = response.json()
        results = []
        
        # Process the first result
        if 'AbstractText' in data and data['AbstractText']:
            results.append({
                'title': data['Heading'] or 'No Title',
                'url': data['AbstractURL'] or f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
                'snippet': data['AbstractText'],
                'source': 'duckduckgo'
            })
            
        # Process related topics
        for topic in data.get('RelatedTopics', [])[:num_results - 1]:
            if 'FirstURL' in topic and 'Text' in topic:
                results.append({
                    'title': topic.get('Text', 'No Title').split(' - ')[0],
                    'url': topic['FirstURL'],
                    'snippet': topic.get('Text', ''),
                    'source': 'duckduckgo'
                })
                
        return results[:num_results]
        """
        
        # Fall back to mock if real search is not implemented
        return self._mock_search(query, num_results)
    
    def _mock_search(self, query: str, num_results: int) -> List[WebSearchResult]:
        """
        Generate mock search results for offline use.
        
        Args:
            query: The search query string (used to customize mock results)
            num_results: Maximum number of results to return
            
        Returns:
            List of mock search results
        """
        # Create a deterministic but varied result based on the query
        query_hash = hash(query) % 1000
        results = []
        
        for i in range(min(num_results, len(self.mock_data))):
            # Modify the mock data based on query to make it look more realistic
            result = self.mock_data[i].copy()
            result["title"] = f"{query.title()}: {result['title']}"
            result["snippet"] = f"Result for '{query}'. {result['snippet']} Query hash: {query_hash}."
            results.append(WebSearchResult(**result))
            
        return results
    
    async def close(self):
        """Clean up resources."""
        await self.client.aclose()

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Create an instance with offline mode
        searcher = WebSearchTool(offline=True)
        
        try:
            # Perform a search
            results = await searcher.search("test query", num_results=2)
            
            # Print the results
            for i, result in enumerate(results, 1):
                print(f"\nResult {i}:")
                print(f"Title: {result['title']}")
                print(f"URL: {result['url']}")
                print(f"Snippet: {result['snippet']}")
                print(f"Source: {result['source']}")
        finally:
            # Clean up
            await searcher.close()
    
    asyncio.run(main())
