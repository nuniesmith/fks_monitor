"""
Test results endpoints.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any

from src.main import get_test_collector
from src.services.test_collector import TestCollector

router = APIRouter()


@router.get("")
async def get_all_tests(
    test_collector: TestCollector = Depends(get_test_collector)
) -> Dict[str, Any]:
    """Get all test results."""
    return {
        "tests": test_collector.get_all_tests(),
        "count": len(test_collector.get_all_tests())
    }

