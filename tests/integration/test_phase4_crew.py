"""Test script for Phase 4: First Crew Prototype.

Verifies that the Research crew is properly registered and can be executed.
"""

import asyncio
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from omni.registry import get_crew_registry
from omni.core.logging import configure_logging

configure_logging()


def test_crew_discovery():
    """Test that crews are discovered properly."""
    print("=" * 60)
    print("Test 1: Crew Discovery")
    print("=" * 60)

    registry = get_crew_registry()
    crews = registry.list_available()

    print(f"\nDiscovered {len(crews)} crew(s):")
    for crew in crews:
        print(f"  - {crew['name']}: {crew['description']}")
        print(f"    Input schema: {crew['input_schema']}")
        print(f"    Output schema: {crew['output_schema']}")

    # Check if research crew is registered
    if registry.is_registered("research"):
        print("\n✓ Research crew is registered")
    else:
        print("\n✗ Research crew NOT found")
        return False

    return True


def test_research_crew_info():
    """Test getting info about the research crew."""
    print("\n" + "=" * 60)
    print("Test 2: Research Crew Info")
    print("=" * 60)

    registry = get_crew_registry()
    info = registry.get_info("research")

    if info:
        print(f"\nCrew Name: {info['name']}")
        print(f"Description: {info['description']}")
        print(f"Class: {info['class_name']}")
        print(f"Agent Count: {info.get('agent_count', 'N/A')}")
        print("\n✓ Successfully retrieved crew info")
        return True
    else:
        print("\n✗ Failed to get crew info")
        return False


@pytest.mark.asyncio
async def test_research_crew_execution():
    """Test executing the research crew."""
    print("\n" + "=" * 60)
    print("Test 3: Research Crew Execution")
    print("=" * 60)

    registry = get_crew_registry()

    test_input = {
        "query": "What are the key differences between Python and JavaScript for web development?",
        "depth": "quick",
        "sources_required": 3,
    }

    print(f"\nInput: {test_input}")
    print("\nExecuting research crew (this may take a while)...")
    print(
        "Note: This requires Ollama to be running with gemma3:12b and llama3.1:8b models"
    )

    try:
        result = registry.execute("research", test_input)

        print("\n✓ Crew execution completed")
        print(f"\nResult keys: {list(result.keys())}")

        if "summary" in result:
            print(f"\nSummary preview: {result['summary'][:200]}...")

        if "key_findings" in result:
            print(f"Key findings: {len(result['key_findings'])} items")

        if "confidence_score" in result:
            print(f"Confidence score: {result['confidence_score']}")

        return True

    except Exception as e:
        print(f"\n✗ Crew execution failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Phase 4: First Crew Prototype - Test Suite")
    print("=" * 60)

    results = []

    # Test 1: Discovery
    results.append(("Crew Discovery", test_crew_discovery()))

    # Test 2: Crew Info
    results.append(("Research Crew Info", test_research_crew_info()))

    # Test 3: Execution (requires Ollama)
    print("\n" + "=" * 60)
    print("Note: Test 3 requires Ollama to be running with the following models:")
    print("  - gemma3:12b (for web researcher and content analyzer)")
    print("  - llama3.1:8b (for fact checker)")
    print("=" * 60)

    try:
        execution_result = asyncio.run(test_research_crew_execution())
        results.append(("Research Crew Execution", execution_result))
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        results.append(("Research Crew Execution", False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    all_passed = all(r[1] for r in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("All tests PASSED ✓")
    else:
        print("Some tests FAILED ✗")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
