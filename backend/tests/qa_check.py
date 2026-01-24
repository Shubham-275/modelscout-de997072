
import unittest
import sys
import os
import json
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from phase2.mino_analyst import MinoAnalyst

class TestMinoAnalystQA(unittest.TestCase):
    def setUp(self):
        self.analyst = MinoAnalyst()
        # Mock the actual API call to avoid costs and dependencies
        self.analyst._call_mino = MagicMock(return_value='{"recommended_model": "Test Model", "confidence": "high"}')

    def test_parallel_scouts_execution(self):
        """Verify that _run_parallel_scouts correctly executes and yields results."""
        scouts = [
            {"name": "Scout A", "prompt": "Task A"},
            {"name": "Scout B", "prompt": "Task B"}
        ]
        
        # We need to test the generator
        events = list(self.analyst._run_parallel_scouts(scouts))
        
        logs = [e for e in events if e['type'] == 'log']
        results = [e for e in events if e['type'] == 'internal_complete']
        
        print(f"\n[QA] Logs captured: {len(logs)}")
        print(f"[QA] Results captured: {len(results)}")
        
        self.assertTrue(len(logs) >= 2, "Should have at least start logs")
        self.assertTrue(len(results) == 1, "Should have exactly one completion event")
        
        data = results[0]['data']
        self.assertIn("Scout A", data)
        self.assertIn("Scout B", data)
        print("[QA] Parallel execution verified successfully.")

    def test_benchmark_stream_structure(self):
        """Verify the full stream structure."""
        print("\n[QA] Testing Benchmark Stream Flow...")
        generator = self.analyst.generate_benchmark_report_stream("QA Test Model")
        
        has_logs = False
        has_result = False
        
        # We mock the aggregator call too
        self.analyst._call_mino = MagicMock(return_value='{"model_name": "QA Test Model", "summary": "Good"}')
        
        try:
            for event in generator:
                if event['type'] == 'log':
                    has_logs = True
                    # print(f"Log: {event['message']}")
                if event['type'] == 'result':
                    has_result = True
                    print(f"[QA] Final Result: {event['data']}")
        except Exception as e:
            self.fail(f"Stream failed with error: {e}")
            
        self.assertTrue(has_logs, "Stream should yield log events")
        self.assertTrue(has_result, "Stream should yield a final result")
        print("[QA] Benchmark stream flow verified.")

if __name__ == '__main__':
    unittest.main()
