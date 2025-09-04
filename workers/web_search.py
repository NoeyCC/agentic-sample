"""
Web Search Worker implementation.

This module contains the WebSearchWorker class which is responsible for
performing web searches and processing the results.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from core.types import WorkerType, WorkerResult, WorkerResponse
from tools.web_search_tool import WebSearchTool

logger = logging.getLogger(__name__)

@dataclass
class SearchConfig:
    """Configuration for web search."""
    num_results: int = 3
    include_domains: Optional[List[str]] = None
    exclude_domains: Optional[List[str]] = None
    search_language: str = "en"

class WebSearchWorker:
    """
    Worker that performs web searches and processes the results.
    
    This worker uses the WebSearchTool to perform searches and then
    processes the results into a structured format.
    """
    
    worker_type = WorkerType.WEB_SEARCH
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the WebSearchWorker.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = self._parse_config(config or {})
        self.search_tool = WebSearchTool(offline=True)
        
    def _parse_config(self, config: Dict[str, Any]) -> SearchConfig:
        """
        Parse and validate the worker configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            SearchConfig instance
        """
        return SearchConfig(
            num_results=config.get("num_results", 3),
            include_domains=config.get("include_domains"),
            exclude_domains=config.get("exclude_domains"),
            search_language=config.get("search_language", "en")
        )
    
    async def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> WorkerResponse:
        """
        Process a search query and return results.
        
        Args:
            query: The search query string
            context: Optional context dictionary
            
        Returns:
            WorkerResponse containing the search results or an error
        """
        try:
            logger.info(f"Processing web search query: {query}")
            
            # Perform the search
            search_results = await self.search_tool.search(
                query,
                num_results=self.config.num_results
            )
            
            # Filter results by domain if needed
            if self.config.include_domains or self.config.exclude_domains:
                search_results = self._filter_results_by_domain(
                    search_results,
                    include=self.config.include_domains,
                    exclude=self.config.exclude_domains
                )
            
            # Format the results
            formatted_results = self._format_results(search_results)
            
            # Create metadata
            metadata = {
                "num_results": len(search_results),
                "query": query,
                "config": {
                    "num_results": self.config.num_results,
                    "include_domains": self.config.include_domains,
                    "exclude_domains": self.config.exclude_domains,
                    "search_language": self.config.search_language
                }
            }
            
            return WorkerResponse(
                success=True,
                result=WorkerResult(
                    content=formatted_results,
                    metadata=metadata,
                    source=str(self.worker_type)
                )
            )
            
        except Exception as e:
            logger.error(f"Error in WebSearchWorker: {str(e)}", exc_info=True)
            return WorkerResponse(
                success=False,
                error=f"Web search failed: {str(e)}"
            )
    
    def _filter_results_by_domain(
        self, 
        results: List[Dict[str, Any]],
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter search results by domain.
        
        Args:
            results: List of search results
            include: List of domains to include (if None, all included)
            exclude: List of domains to exclude
            
        Returns:
            Filtered list of search results
        """
        if not include and not exclude:
            return results
            
        filtered = []
        
        for result in results:
            url = result.get('url', '').lower()
            
            # Check include domains
            if include and not any(domain.lower() in url for domain in include):
                continue
                
            # Check exclude domains
            if exclude and any(domain.lower() in url for domain in exclude):
                continue
                
            filtered.append(result)
            
        return filtered
    
    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Format search results as a markdown string.
        
        Args:
            results: List of search results
            
        Returns:
            Formatted markdown string
        """
        if not results:
            return "No search results found."
            
        formatted = ["## Search Results\n"]
        
        for i, result in enumerate(results, 1):
            formatted.append(f"### {i}. {result.get('title', 'No Title')}")
            formatted.append(f"**URL:** {result.get('url', 'N/A')}")
            formatted.append(f"**Snippet:** {result.get('snippet', 'No snippet available.')}")
            formatted.append(f"**Source:** {result.get('source', 'unknown')}\n")
        
        return "\n".join(formatted)
    
    async def close(self):
        """Clean up resources."""
        await self.search_tool.close()

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Create a worker
        worker = WebSearchWorker({
            "num_results": 2,
            "exclude_domains": ["wikipedia.org"]
        })
        
        try:
            # Process a search query
            response = await worker.process("Python 3.11 features")
            
            if response.success and response.result:
                print("Search successful!")
                print("Results:")
                print(response.result.content)
                
                print("\nMetadata:")
                for key, value in response.result.metadata.items():
                    print(f"{key}: {value}")
            else:
                print(f"Search failed: {response.error}")
                
        finally:
            # Clean up
            await worker.close()
    
    asyncio.run(main())
