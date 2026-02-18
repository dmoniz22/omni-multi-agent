"""Main LangGraph workflow definition for OMNI.

Assembles the state graph with all nodes, edges, and conditional routing.
"""
from langgraph.graph import StateGraph, END

from omni.core.state import OmniState
from omni.orchestrator.nodes.query_analyzer import query_analyzer
from omni.orchestrator.nodes.orchestrator_decision import orchestrator_decision
from omni.orchestrator.nodes.department_router import department_router
from omni.orchestrator.nodes.crew_execution import crew_execution
from omni.orchestrator.nodes.validation import validation
from omni.orchestrator.nodes.response_collator import response_collator
from omni.orchestrator.nodes.output import output
from omni.orchestrator.edges import (
    route_after_decision,
    route_after_validation,
)
from omni.core.logging import get_logger

logger = get_logger("omni.orchestrator.graph")


def create_workflow() -> StateGraph:
    """Create and configure the LangGraph workflow.
    
    Returns:
        StateGraph: Configured workflow graph
    """
    # Create the graph
    workflow = StateGraph(OmniState)
    
    # Add nodes
    workflow.add_node("query_analyzer", query_analyzer)
    workflow.add_node("orchestrator_decision", orchestrator_decision)
    workflow.add_node("department_router", department_router)
    workflow.add_node("crew_execution", crew_execution)
    workflow.add_node("validation", validation)
    workflow.add_node("response_collator", response_collator)
    workflow.add_node("output", output)
    
    # Set entry point
    workflow.set_entry_point("query_analyzer")
    
    # Add edges
    # query_analyzer -> orchestrator_decision (always)
    workflow.add_edge("query_analyzer", "orchestrator_decision")
    
    # orchestrator_decision -> conditional
    workflow.add_conditional_edges(
        "orchestrator_decision",
        route_after_decision,
        {
            "department_router": "department_router",
            "response_collator": "response_collator",
        }
    )
    
    # department_router -> crew_execution (always)
    workflow.add_edge("department_router", "crew_execution")
    
    # crew_execution -> validation (always)
    workflow.add_edge("crew_execution", "validation")
    
    # validation -> orchestrator_decision (always, for now)
    workflow.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "orchestrator_decision": "orchestrator_decision",
        }
    )
    
    # response_collator -> output (always)
    workflow.add_edge("response_collator", "output")
    
    # output -> END (terminal)
    workflow.add_edge("output", END)
    
    logger.info("Workflow graph created")
    
    return workflow


# Global workflow instance
_workflow = None


def get_workflow():
    """Get the compiled workflow.
    
    Returns:
        CompiledStateGraph: Compiled workflow ready for execution
    """
    global _workflow
    
    if _workflow is None:
        workflow = create_workflow()
        _workflow = workflow.compile()
        logger.info("Workflow compiled")
    
    return _workflow
