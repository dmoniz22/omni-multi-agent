"""Query analyzer node for the LangGraph workflow.

Analyzes the user task to determine intent, required departments, and workflow pattern.
"""
import json
from datetime import datetime

from omni.core.state import OmniState, StepType, QueryAnalysis, Complexity, WorkflowPattern
from omni.core.models import get_model
from omni.core.logging import get_logger

logger = get_logger("omni.orchestrator.nodes.query_analyzer")


SYSTEM_PROMPT = """You are the Query Analyzer for the OMNI multi-agent orchestration system.

Your task is to analyze the user's input and determine:
1. The intent of the query
2. Which departments (crews) are needed
3. The complexity level
4. The workflow pattern

Available departments:
- github: GitHub operations, repository analysis, code review
- research: Web research, content analysis, fact-checking
- social: Social media content creation and optimization
- analysis: Data analysis, pattern recognition, insights
- writing: Long-form writing, editing, documentation
- coding: Code generation, refactoring, architecture

Complexity levels:
- simple: Single task, one department
- moderate: Multiple related tasks, 1-2 departments
- complex: Complex workflow, multiple departments, iteration needed

Workflow patterns:
- single_crew: One department handles everything
- sequential: Multiple departments in sequence
- parallel: Multiple departments working simultaneously
- iterative: Loop back for refinement

Respond with JSON matching this schema:
{
    "intent": "description of what user wants",
    "required_departments": ["dept1", "dept2"],
    "complexity": "simple|moderate|complex",
    "workflow_pattern": "single_crew|sequential|parallel|iterative",
    "parameters": {"key": "value"}
}"""


async def query_analyzer(state: OmniState) -> dict:
    """Analyze the user query.
    
    Args:
        state: Current workflow state
        
    Returns:
        Dict with updates to state (query_analysis)
    """
    logger.info("Analyzing query", task_id=state["task_id"])
    
    try:
        # Get model for query analysis
        model = get_model("qwen3:14b", temperature=0.3)
        
        # Build prompt
        messages = [
            ("system", SYSTEM_PROMPT),
            ("human", f"Task: {state['original_task']}")
        ]
        
        # Call LLM
        response = await model.ainvoke(messages)
        content = response.content
        
        # Parse JSON response
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        analysis_data = json.loads(content.strip())
        
        # Create QueryAnalysis object
        query_analysis = QueryAnalysis(
            intent=analysis_data["intent"],
            required_departments=analysis_data["required_departments"],
            complexity=Complexity(analysis_data["complexity"]),
            workflow_pattern=WorkflowPattern(analysis_data["workflow_pattern"]),
            parameters=analysis_data.get("parameters", {})
        )
        
        logger.info(
            "Query analysis complete",
            intent=query_analysis.intent,
            departments=query_analysis.required_departments,
            complexity=query_analysis.complexity.value
        )
        
        return {
            "query_analysis": query_analysis.model_dump(),
            "status": "running",
            "history": [{
                "step_number": state["control"]["current_step"],
                "step_type": StepType.QUERY_ANALYSIS,
                "node_name": "query_analyzer",
                "input_data": {"task": state["original_task"]},
                "output_data": query_analysis.model_dump(),
                "timestamp": datetime.utcnow().isoformat(),
                "duration_ms": 0,
                "model_used": "qwen3:14b"
            }]
        }
        
    except Exception as e:
        logger.error("Query analysis failed", error=str(e))
        # Return a default analysis on error
        return {
            "query_analysis": QueryAnalysis(
                intent="general_query",
                required_departments=["research"],
                complexity=Complexity.SIMPLE,
                workflow_pattern=WorkflowPattern.SINGLE_CREW,
                parameters={}
            ).model_dump(),
            "status": "running",
            "history": [{
                "step_number": state["control"]["current_step"],
                "step_type": StepType.QUERY_ANALYSIS,
                "node_name": "query_analyzer",
                "input_data": {"task": state["original_task"]},
                "output_data": {"error": str(e), "fallback": True},
                "timestamp": datetime.utcnow().isoformat(),
                "duration_ms": 0,
                "model_used": "qwen3:14b",
                "error": str(e)
            }]
        }
