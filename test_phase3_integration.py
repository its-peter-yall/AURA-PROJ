#!/usr/bin/env python
"""
Phase 3: Comprehensive Integration Testing Script
==================================================

This script tests the fixes implemented in Phase 1 (Gemini 3 Thinking Mode)
and Phase 2 (Conversation History) for the AURA-CHAT RAG engine.

Tests:
1. Gemini 3 Thinking Mode
2. Conversation History ("SAY MY NAME")
3. History Window Bounds
4. Thinking + Multi-Turn Conversation
5. Gemini 2.5 Regression
6. Non-Thinking Mode Fallback

Usage:
    python test_phase3_integration.py
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "AURA-CHAT"))

from backend.rag_engine import RAGEngine
from backend.graph_manager import GraphManager
from backend.chat_manager import ChatManager
from backend.utils.logging_config import setup_logging
from backend.utils.config import config

logger = setup_logging("phase3_integration_test")


class TestResults:
    """Test results tracker"""

    def __init__(self):
        self.tests = {}
        self.evidence = {}

    def record_test(
        self, test_name: str, status: str, passed: bool, notes: str, evidence: Any
    ):
        self.tests[test_name] = {
            "status": status,
            "passed": passed,
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
        }
        self.evidence[test_name] = evidence

    def summary(self) -> Dict[str, Any]:
        total = len(self.tests)
        passed = sum(1 for t in self.tests.values() if t["passed"])
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "tests": self.tests,
        }


async def test_1_gemini3_thinking_mode(rag_engine: RAGEngine, results: TestResults):
    """Test 1: Verify Gemini 3 thinking mode works without errors"""
    test_name = "Test 1: Gemini 3 Thinking Mode"
    logger.info(f"\n{'=' * 80}\n{test_name}\n{'=' * 80}")

    try:
        # Set model to Gemini 3
        rag_engine.set_model("gemini-3-flash-preview")

        # Query with thinking mode
        query = "Explain the relationship between thermodynamics and quantum mechanics in detail"
        session_id = f"test_gemini3_{datetime.now().timestamp()}"

        logger.info(f"Querying with: {query}")
        response = await rag_engine.query(
            user_query=query, session_id=session_id, mode="tutor", enable_thinking=True
        )

        # Check results
        passed = True
        notes = []

        # Verify response exists
        if not response.get("answer"):
            passed = False
            notes.append("❌ No answer returned")
        else:
            notes.append(f"✅ Response received ({len(response['answer'])} chars)")

        # Check model used
        model_used = response.get("model_used", "")
        if "gemini-3" in model_used.lower():
            notes.append(f"✅ Correct model used: {model_used}")
        else:
            passed = False
            notes.append(f"❌ Wrong model used: {model_used}")

        # Check for thought summary (thinking mode indicator)
        thought_summary = response.get("thought_summary", "")
        if thought_summary:
            notes.append(f"✅ Thought summary present ({len(thought_summary)} chars)")
        else:
            notes.append("⚠️ No thought summary (thinking may not be active)")

        results.record_test(
            test_name,
            "COMPLETED",
            passed,
            "\n".join(notes),
            {
                "query": query,
                "model_used": model_used,
                "answer_length": len(response.get("answer", "")),
                "thought_summary_length": len(thought_summary),
                "sources_count": len(response.get("sources", [])),
            },
        )

        logger.info(f"Test 1 Result: {'PASSED' if passed else 'FAILED'}")
        logger.info(f"Notes:\n{chr(10).join(notes)}")

    except Exception as e:
        logger.error(f"Test 1 FAILED with exception: {e}", exc_info=True)
        results.record_test(
            test_name,
            "FAILED",
            False,
            f"Exception: {str(e)}",
            {"error": str(e), "type": type(e).__name__},
        )


async def test_2_conversation_history_say_my_name(
    rag_engine: RAGEngine, results: TestResults
):
    """Test 2: Verify model remembers conversation context"""
    test_name = "Test 2: Conversation History (SAY MY NAME)"
    logger.info(f"\n{'=' * 80}\n{test_name}\n{'=' * 80}")

    try:
        session_id = f"test_say_my_name_{datetime.now().timestamp()}"

        # Step 1: Introduce name
        logger.info("Step 1: Introducing name")
        response1 = await rag_engine.query(
            user_query="My name is Alexander Hamilton",
            session_id=session_id,
            mode="tutor",
            enable_thinking=False,
        )
        logger.info(f"Response 1: {response1.get('answer', '')[:200]}")

        # Step 2: Ask unrelated questions
        logger.info("Step 2: Asking unrelated questions")
        await rag_engine.query(
            user_query="What is machine learning?",
            session_id=session_id,
            mode="tutor",
            enable_thinking=False,
        )

        await rag_engine.query(
            user_query="Explain neural networks",
            session_id=session_id,
            mode="tutor",
            enable_thinking=False,
        )

        # Step 3: Ask for name recall
        logger.info("Step 3: Asking to recall name")
        response_final = await rag_engine.query(
            user_query="SAY MY NAME",
            session_id=session_id,
            mode="tutor",
            enable_thinking=False,
        )

        answer = response_final.get("answer", "").lower()
        logger.info(f"Final Response: {answer[:500]}")

        # Check if name is recalled
        name_recalled = "alexander hamilton" in answer or "hamilton" in answer

        passed = name_recalled
        notes = []

        if name_recalled:
            notes.append("✅ Model correctly recalled the name 'Alexander Hamilton'")
        else:
            notes.append("❌ Model did NOT recall the name")
            notes.append(f"Response: {answer[:200]}")

        # Check history length
        history = rag_engine.chat_manager.get_last_n_messages(session_id, n=100)
        notes.append(f"✅ History contains {len(history)} messages")

        results.record_test(
            test_name,
            "COMPLETED",
            passed,
            "\n".join(notes),
            {
                "session_id": session_id,
                "name_recalled": name_recalled,
                "final_response": answer[:500],
                "history_length": len(history),
            },
        )

        logger.info(f"Test 2 Result: {'PASSED' if passed else 'FAILED'}")
        logger.info(f"Notes:\n{chr(10).join(notes)}")

    except Exception as e:
        logger.error(f"Test 2 FAILED with exception: {e}", exc_info=True)
        results.record_test(
            test_name,
            "FAILED",
            False,
            f"Exception: {str(e)}",
            {"error": str(e), "type": type(e).__name__},
        )


async def test_3_history_window_bounds(rag_engine: RAGEngine, results: TestResults):
    """Test 3: Verify 50-message window works correctly"""
    test_name = "Test 3: History Window Bounds"
    logger.info(f"\n{'=' * 80}\n{test_name}\n{'=' * 80}")

    try:
        session_id = f"test_window_{datetime.now().timestamp()}"

        # Create 60 messages
        logger.info("Creating 60 messages...")
        for i in range(30):
            await rag_engine.query(
                user_query=f"Question {i + 1}: What is concept number {i + 1}?",
                session_id=session_id,
                mode="assistant",
                enable_thinking=False,
            )
            if i % 10 == 0:
                logger.info(f"  Created {i + 1} message pairs...")

        # Check history
        full_history = rag_engine.chat_manager.get_last_n_messages(session_id, n=100)
        window_history = rag_engine.chat_manager.get_last_n_messages(session_id, n=50)

        passed = True
        notes = []

        notes.append(f"✅ Full history contains {len(full_history)} messages")
        notes.append(f"✅ Window history contains {len(window_history)} messages")

        if len(window_history) == 50:
            notes.append("✅ Window correctly limited to 50 messages")
        else:
            passed = False
            notes.append(f"❌ Window size is {len(window_history)}, expected 50")

        # Verify window contains recent messages
        if window_history and "Question 30" in window_history[-1].get("content", ""):
            notes.append("✅ Window contains most recent messages")
        else:
            notes.append("⚠️ Window may not contain most recent messages")

        results.record_test(
            test_name,
            "COMPLETED",
            passed,
            "\n".join(notes),
            {
                "session_id": session_id,
                "full_history_length": len(full_history),
                "window_history_length": len(window_history),
            },
        )

        logger.info(f"Test 3 Result: {'PASSED' if passed else 'FAILED'}")
        logger.info(f"Notes:\n{chr(10).join(notes)}")

    except Exception as e:
        logger.error(f"Test 3 FAILED with exception: {e}", exc_info=True)
        results.record_test(
            test_name,
            "FAILED",
            False,
            f"Exception: {str(e)}",
            {"error": str(e), "type": type(e).__name__},
        )


async def test_4_thinking_multi_turn(rag_engine: RAGEngine, results: TestResults):
    """Test 4: Verify thinking mode works with multi-turn conversation"""
    test_name = "Test 4: Thinking Mode with Multi-Turn Conversation"
    logger.info(f"\n{'=' * 80}\n{test_name}\n{'=' * 80}")

    try:
        # Use Gemini 3 for thinking
        rag_engine.set_model("gemini-3-flash-preview")
        session_id = f"test_thinking_multiturn_{datetime.now().timestamp()}"

        # Multi-turn conversation
        queries = [
            "What are the main principles of machine learning?",
            "Explain how neural networks implement one of those principles",
            "How does backpropagation relate to gradient descent?",
        ]

        responses = []
        for i, query in enumerate(queries, 1):
            logger.info(f"Query {i}: {query}")
            response = await rag_engine.query(
                user_query=query,
                session_id=session_id,
                mode="tutor",
                enable_thinking=True,
            )
            responses.append(response)
            logger.info(f"Response {i} length: {len(response.get('answer', ''))} chars")

        passed = True
        notes = []

        # Check all responses received
        if all(r.get("answer") for r in responses):
            notes.append(f"✅ All {len(queries)} queries received responses")
        else:
            passed = False
            notes.append("❌ Some queries did not receive responses")

        # Check thinking mode was active
        thought_counts = sum(1 for r in responses if r.get("thought_summary"))
        notes.append(
            f"✅ {thought_counts}/{len(queries)} responses had thought summaries"
        )

        # Check context preservation
        last_response = responses[-1].get("answer", "").lower()
        context_preserved = any(
            keyword in last_response for keyword in ["gradient", "learning", "neural"]
        )
        if context_preserved:
            notes.append("✅ Context from previous turns appears to be preserved")
        else:
            notes.append("⚠️ Context preservation unclear from response content")

        results.record_test(
            test_name,
            "COMPLETED",
            passed,
            "\n".join(notes),
            {
                "session_id": session_id,
                "queries": queries,
                "response_lengths": [len(r.get("answer", "")) for r in responses],
                "thought_summary_count": thought_counts,
            },
        )

        logger.info(f"Test 4 Result: {'PASSED' if passed else 'FAILED'}")
        logger.info(f"Notes:\n{chr(10).join(notes)}")

    except Exception as e:
        logger.error(f"Test 4 FAILED with exception: {e}", exc_info=True)
        results.record_test(
            test_name,
            "FAILED",
            False,
            f"Exception: {str(e)}",
            {"error": str(e), "type": type(e).__name__},
        )


async def test_5_gemini25_regression(rag_engine: RAGEngine, results: TestResults):
    """Test 5: Verify Gemini 2.5 models still work correctly"""
    test_name = "Test 5: Gemini 2.5 Regression"
    logger.info(f"\n{'=' * 80}\n{test_name}\n{'=' * 80}")

    try:
        # Set model to Gemini 2.5
        rag_engine.set_model("gemini-2.5-flash-lite")

        # Query with thinking mode
        query = "Explain the concept of gradient descent in machine learning"
        session_id = f"test_gemini25_{datetime.now().timestamp()}"

        logger.info(f"Querying with: {query}")
        response = await rag_engine.query(
            user_query=query, session_id=session_id, mode="tutor", enable_thinking=True
        )

        # Check results
        passed = True
        notes = []

        # Verify response exists
        if not response.get("answer"):
            passed = False
            notes.append("❌ No answer returned")
        else:
            notes.append(f"✅ Response received ({len(response['answer'])} chars)")

        # Check model used
        model_used = response.get("model_used", "")
        if "gemini-2.5" in model_used.lower():
            notes.append(f"✅ Correct model used: {model_used}")
        else:
            passed = False
            notes.append(f"❌ Wrong model used: {model_used}")

        # Check for thought summary
        thought_summary = response.get("thought_summary", "")
        if thought_summary:
            notes.append(f"✅ Thought summary present ({len(thought_summary)} chars)")
        else:
            notes.append("⚠️ No thought summary (thinking may not be active)")

        results.record_test(
            test_name,
            "COMPLETED",
            passed,
            "\n".join(notes),
            {
                "query": query,
                "model_used": model_used,
                "answer_length": len(response.get("answer", "")),
                "thought_summary_length": len(thought_summary),
                "sources_count": len(response.get("sources", [])),
            },
        )

        logger.info(f"Test 5 Result: {'PASSED' if passed else 'FAILED'}")
        logger.info(f"Notes:\n{chr(10).join(notes)}")

    except Exception as e:
        logger.error(f"Test 5 FAILED with exception: {e}", exc_info=True)
        results.record_test(
            test_name,
            "FAILED",
            False,
            f"Exception: {str(e)}",
            {"error": str(e), "type": type(e).__name__},
        )


async def test_6_non_thinking_fallback(rag_engine: RAGEngine, results: TestResults):
    """Test 6: Verify non-thinking mode works correctly"""
    test_name = "Test 6: Non-Thinking Mode Fallback"
    logger.info(f"\n{'=' * 80}\n{test_name}\n{'=' * 80}")

    try:
        # Use any model with thinking disabled
        rag_engine.set_model("gemini-2.5-flash-lite")

        query = "What is machine learning?"
        session_id = f"test_non_thinking_{datetime.now().timestamp()}"

        logger.info(f"Querying with thinking DISABLED: {query}")
        response = await rag_engine.query(
            user_query=query, session_id=session_id, mode="tutor", enable_thinking=False
        )

        # Check results
        passed = True
        notes = []

        # Verify response exists
        if not response.get("answer"):
            passed = False
            notes.append("❌ No answer returned")
        else:
            notes.append(f"✅ Response received ({len(response['answer'])} chars)")

        # Should NOT have thought summary
        thought_summary = response.get("thought_summary", "")
        if not thought_summary:
            notes.append("✅ No thought summary (thinking correctly disabled)")
        else:
            notes.append(
                f"⚠️ Thought summary present despite thinking disabled ({len(thought_summary)} chars)"
            )

        results.record_test(
            test_name,
            "COMPLETED",
            passed,
            "\n".join(notes),
            {
                "query": query,
                "model_used": response.get("model_used", ""),
                "answer_length": len(response.get("answer", "")),
                "thought_summary_length": len(thought_summary),
            },
        )

        logger.info(f"Test 6 Result: {'PASSED' if passed else 'FAILED'}")
        logger.info(f"Notes:\n{chr(10).join(notes)}")

    except Exception as e:
        logger.error(f"Test 6 FAILED with exception: {e}", exc_info=True)
        results.record_test(
            test_name,
            "FAILED",
            False,
            f"Exception: {str(e)}",
            {"error": str(e), "type": type(e).__name__},
        )


async def main():
    """Run all integration tests"""
    logger.info(f"\n{'=' * 80}\nPhase 3: Comprehensive Integration Testing\n{'=' * 80}")
    logger.info(f"Start Time: {datetime.now().isoformat()}")
    logger.info(f"Python Version: {sys.version}")
    logger.info(
        f"Config: Thinking Enabled={config.ENABLE_THINKING}, "
        f"Thinking Budget={config.THINKING_BUDGET}, "
        f"Thinking Level={config.THINKING_LEVEL}"
    )

    results = TestResults()

    try:
        # Initialize graph manager and RAG engine
        logger.info("\nInitializing services...")
        graph_manager = GraphManager()
        await graph_manager.connect()
        rag_engine = RAGEngine(graph_manager)

        logger.info("Services initialized successfully\n")

        # Run tests
        await test_1_gemini3_thinking_mode(rag_engine, results)
        await test_2_conversation_history_say_my_name(rag_engine, results)
        await test_3_history_window_bounds(rag_engine, results)
        await test_4_thinking_multi_turn(rag_engine, results)
        await test_5_gemini25_regression(rag_engine, results)
        await test_6_non_thinking_fallback(rag_engine, results)

        # Close connections
        await graph_manager.close()

    except Exception as e:
        logger.error(f"Test execution failed: {e}", exc_info=True)

    # Print summary
    summary = results.summary()
    logger.info(f"\n{'=' * 80}\nTest Summary\n{'=' * 80}")
    logger.info(f"Total Tests: {summary['total']}")
    logger.info(f"Passed: {summary['passed']}")
    logger.info(f"Failed: {summary['failed']}")
    logger.info(f"Success Rate: {summary['passed'] / summary['total'] * 100:.1f}%")

    # Save results
    output_file = "test-results/phase3-test-evidence.json"
    with open(output_file, "w") as f:
        json.dump(
            {
                "summary": summary,
                "evidence": results.evidence,
                "timestamp": datetime.now().isoformat(),
            },
            f,
            indent=2,
        )

    logger.info(f"\nResults saved to: {output_file}")
    logger.info(f"End Time: {datetime.now().isoformat()}")

    # Exit with appropriate code
    sys.exit(0 if summary["failed"] == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
