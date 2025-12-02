"""
Test results endpoints.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any

from src.services.test_collector import TestCollector

router = APIRouter()


def get_test_collector() -> TestCollector:
    """Get test collector instance (lazy import to avoid circular dependency)."""
    # Lazy import to avoid circular dependency
    import src.main as main_module
    if main_module.test_collector is None:
        raise RuntimeError("Test collector not initialized")
    return main_module.test_collector


@router.get("")
async def get_all_tests(
    test_collector: TestCollector = Depends(get_test_collector)
) -> Dict[str, Any]:
    """Get all test results."""
    return {
        "tests": test_collector.get_all_tests(),
        "count": len(test_collector.get_all_tests())
    }

