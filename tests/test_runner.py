"""
Comprehensive test runner for ArgosOS
"""
import pytest
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_all_tests():
    """Run all tests with comprehensive reporting"""
    print("🧪 Running Comprehensive ArgosOS Test Suite")
    print("=" * 50)
    
    # Test configuration
    test_args = [
        "tests/",
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker handling
        "--disable-warnings",  # Disable warnings for cleaner output
        "--color=yes",  # Colored output
        "-x",  # Stop on first failure
    ]
    
    # Run tests
    exit_code = pytest.main(test_args)
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code: {exit_code}")
    
    return exit_code

def run_specific_test(test_file):
    """Run a specific test file"""
    print(f"🧪 Running specific test: {test_file}")
    print("=" * 50)
    
    test_args = [
        f"tests/{test_file}",
        "-v",
        "--tb=short",
        "--color=yes",
    ]
    
    exit_code = pytest.main(test_args)
    return exit_code

def run_agent_tests():
    """Run only agent tests"""
    return run_specific_test("test_agents_comprehensive.py")

def run_api_tests():
    """Run only API tests"""
    return run_specific_test("test_api_integration.py")

def run_llm_mock_tests():
    """Run only LLM mock tests"""
    return run_specific_test("test_llm_mocks.py")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        if test_type == "agents":
            exit_code = run_agent_tests()
        elif test_type == "api":
            exit_code = run_api_tests()
        elif test_type == "llm":
            exit_code = run_llm_mock_tests()
        else:
            print(f"Unknown test type: {test_type}")
            print("Available types: agents, api, llm")
            exit_code = 1
    else:
        exit_code = run_all_tests()
    
    sys.exit(exit_code)
