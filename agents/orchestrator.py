"""
Orchestrator for the agentic workflow.

This module implements the Orchestrator class which coordinates the execution
of different workers based on the user's query and manages the overall workflow.
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from core.types import (
    WorkerType,
    WorkerResult,
    ExecutionPlan,
    BriefOutput,
    APIResponse,
    APIRequest
)
from agents.router import Router
from agents.evaluator import Evaluator
from workers.web_search import WebSearchWorker
from tools.summarizer import Summarizer

logger = logging.getLogger(__name__)

@dataclass
class WorkerConfig:
    """Configuration for worker initialization."""
    config: Dict[str, Any]
    worker_class: Any

class Orchestrator:
    """
    Coordinates the execution of workers and manages the agentic workflow.
    
    Implements the Orchestrator-Worker pattern to manage the execution
    of specialized workers based on the user's query.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Orchestrator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.router = Router()
        self.evaluator = Evaluator()
        self.summarizer = Summarizer()
        
        # Initialize workers
        self.workers = {
            WorkerType.WEB_SEARCH: WebSearchWorker(
                config=self.config.get("web_search", {})
            ),
            # Add other workers here as needed
        }
        
        # Worker registry mapping
        self.worker_registry = {
            WorkerType.WEB_SEARCH: self.workers[WorkerType.WEB_SEARCH],
            # Add other workers here as needed
        }
    
    async def process_request(self, request: APIRequest) -> APIResponse:
        """
        Process an API request and generate a response.
        
        Args:
            request: The API request containing the user query
            
        Returns:
            APIResponse containing the result or an error
        """
        try:
            logger.info(f"Processing request: {request.query}")
            
            # Step 1: Create execution plan
            plan = self._create_execution_plan(request.query)
            logger.info(f"Created execution plan: {plan}")
            
            # Step 2: Execute workers in parallel
            worker_results = await self._execute_workers(plan)
            
            # Step 3: Aggregate and process results
            brief = await self._generate_brief(
                query=request.query,
                worker_results=worker_results
            )
            
            # Step 4: Evaluate the brief
            evaluation = self.evaluator.evaluate_brief(
                brief=brief,
                original_query=request.query
            )
            
            # Step 5: Optimize if needed
            if not evaluation.is_complete and evaluation.score < 0.7:
                logger.info("Brief evaluation failed, attempting to improve...")
                improved_brief = await self._optimize_brief(
                    brief=brief,
                    evaluation=evaluation,
                    original_query=request.query,
                    worker_results=worker_results
                )
                
                if improved_brief:
                    brief = improved_brief
                    evaluation = self.evaluator.evaluate_brief(
                        brief=brief,
                        original_query=request.query
                    )
            
            # Prepare response
            return APIResponse(
                success=True,
                brief=brief,
                metadata={
                    "evaluation_score": evaluation.score,
                    "is_complete": evaluation.is_complete,
                    "worker_count": len(worker_results),
                    "generated_at": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return APIResponse(
                success=False,
                error=f"Failed to process request: {str(e)}"
            )
    
    def _create_execution_plan(self, query: str) -> ExecutionPlan:
        """
        Create an execution plan based on the user's query.
        
        Args:
            query: The user's query string
            
        Returns:
            ExecutionPlan containing the plan details
        """
        plan_data = self.router.create_execution_plan(query)
        return ExecutionPlan(**plan_data)
    
    async def _execute_workers(
        self,
        plan: ExecutionPlan
    ) -> Dict[WorkerType, WorkerResult]:
        """
        Execute the required workers in parallel.
        
        Args:
            plan: The execution plan
            
        Returns:
            Dictionary mapping worker types to their results
        """
        tasks = []
        
        # Create tasks for each required worker
        for worker_type in plan.required_workers:
            if worker_type in self.worker_registry:
                worker = self.worker_registry[worker_type]
                tasks.append(
                    self._execute_worker(worker, worker_type, plan)
                )
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        worker_results = {}
        for worker_type, result in zip(plan.required_workers, results):
            if isinstance(result, Exception):
                logger.error(
                    f"Worker {worker_type} failed: {str(result)}",
                    exc_info=result
                )
            else:
                worker_results[worker_type] = result
        
        return worker_results
    
    async def _execute_worker(
        self,
        worker: Any,
        worker_type: WorkerType,
        plan: ExecutionPlan
    ) -> WorkerResult:
        """
        Execute a single worker and return its result.
        
        Args:
            worker: The worker instance
            worker_type: The type of worker
            plan: The execution plan
            
        Returns:
            The worker's result
        """
        try:
            logger.info(f"Executing worker: {worker_type}")
            
            # Execute the worker with the query and context
            response = await worker.process(plan.query, plan.context)
            
            if not response.success:
                raise Exception(f"Worker {worker_type} failed: {response.error}")
            
            if not response.result:
                raise Exception(f"Worker {worker_type} returned no result")
            
            return response.result
            
        except Exception as e:
            logger.error(f"Error in worker {worker_type}: {str(e)}", exc_info=True)
            raise
    
    async def _generate_brief(
        self,
        query: str,
        worker_results: Dict[WorkerType, WorkerResult]
    ) -> BriefOutput:
        """
        Generate a brief from worker results.
        
        Args:
            query: The original user query
            worker_results: Dictionary of worker results
            
        Returns:
            A BriefOutput object containing the generated brief
        """
        # Combine content from all workers
        combined_content = []
        references = []
        
        for worker_type, result in worker_results.items():
            if result and result.content:
                combined_content.append(f"## {worker_type.value.replace('_', ' ').title()}\n{result.content}")
                
                # Extract references if available
                if hasattr(result, 'metadata') and isinstance(result.metadata, dict):
                    refs = result.metadata.get('references', [])
                    if isinstance(refs, list):
                        references.extend(refs)
        
        # Combine all content
        full_content = "\n\n".join(combined_content)
        
        # Generate a summary if the content is too long
        if len(full_content) > 2000:  # Arbitrary threshold
            summary = await asyncio.get_event_loop().run_in_executor(
                None,
                self.summarizer.summarize,
                full_content
            )
        else:
            summary = full_content
        
        # Create the brief
        return BriefOutput(
            title=f"Brief: {query[:50]}" + ("..." if len(query) > 50 else ""),
            content=summary,
            references=references[:10],  # Limit to 10 references
            generated_at=datetime.utcnow().isoformat()
        )
    
    async def _optimize_brief(
        self,
        brief: BriefOutput,
        evaluation: Any,
        original_query: str,
        worker_results: Dict[WorkerType, WorkerResult]
    ) -> Optional[BriefOutput]:
        """
        Attempt to improve the brief based on evaluation feedback.
        
        Args:
            brief: The original brief
            evaluation: The evaluation result
            original_query: The original user query
            worker_results: Dictionary of worker results
            
        Returns:
            An improved BriefOutput, or None if optimization failed
        """
        logger.info("Attempting to optimize brief...")
        
        try:
            # Get improvement suggestions
            suggestions = self.evaluator.generate_improvement_suggestions(
                evaluation=evaluation,
                brief=brief,
                original_query=original_query
            )
            
            if not suggestions:
                return None
            
            logger.info(f"Optimization suggestions: {suggestions}")
            
            # For this example, we'll just add the suggestions to the brief
            # In a real implementation, you might want to be more sophisticated
            improved_content = (
                f"{brief.content}\n\n"
                f"## Optimization Notes\n"
                f"The following improvements were suggested:\n\n"
                + "\n".join(f"- {suggestion}" for suggestion in suggestions[:3])
            )
            
            return BriefOutput(
                title=brief.title,
                content=improved_content,
                references=brief.references,
                generated_at=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error during brief optimization: {str(e)}", exc_info=True)
            return None
    
    async def close(self):
        """Clean up resources."""
        for worker in self.workers.values():
            if hasattr(worker, 'close') and callable(worker.close):
                await worker.close()

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Create an orchestrator
        orchestrator = Orchestrator()
        
        try:
            # Create a test request
            request = APIRequest(
                query="What are the latest trends in artificial intelligence?"
            )
            
            # Process the request
            response = await orchestrator.process_request(request)
            
            # Print the result
            if response.success and response.brief:
                print("\n=== Generated Brief ===\n")
                print(f"Title: {response.brief.title}")
                print(f"\nContent:\n{response.brief.content}")
                
                if response.brief.references:
                    print("\nReferences:")
                    for i, ref in enumerate(response.brief.references, 1):
                        print(f"{i}. {ref.get('title', 'No title')} - {ref.get('url', 'No URL')}")
                
                if hasattr(response, 'metadata') and response.metadata:
                    print(f"\nMetadata: {response.metadata}")
            else:
                print(f"Error: {response.error}")
                
        finally:
            # Clean up
            await orchestrator.close()
    
    # Run the example
    asyncio.run(main())
