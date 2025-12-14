"""
Lab 5 - Exercise 2: Response Evaluation
========================================

This exercise covers response quality evaluation:
1. ROUGE-1 word overlap (response_match_score)
2. Semantic matching with LLM-as-judge (final_response_match_v2)
3. Understanding evaluation thresholds
4. Comparing different response evaluation approaches

Run: uv run python 02_response_evaluation.py
"""

import asyncio
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# =============================================================================
# Part 1: Understanding Response Evaluation
# =============================================================================

def explain_response_evaluation():
    """Explain response evaluation concepts."""
    print("""
    RESPONSE EVALUATION OVERVIEW
    ============================

    Response evaluation asks: "Did the agent give the RIGHT answer?"

    TWO MAIN APPROACHES:
    --------------------

    1. LEXICAL MATCHING (response_match_score)
       - Uses ROUGE-1 (word overlap)
       - Fast, deterministic
       - Best for: CI/CD, regression testing
       - Limitation: Doesn't understand meaning

       Example:
         Expected: "The temperature is 72 degrees Fahrenheit"
         Actual:   "It's 72°F"
         Score: Low (few overlapping words)

    2. SEMANTIC MATCHING (final_response_match_v2)
       - Uses LLM-as-judge
       - Understands meaning
       - Best for: Quality assessment
       - Limitation: Slower, costs more

       Example:
         Expected: "The temperature is 72 degrees Fahrenheit"
         Actual:   "It's 72°F"
         Score: High (same meaning)

    WHEN TO USE EACH:
    -----------------
    ┌────────────────────────────────────────────────────────────┐
    │  Scenario                    │  Recommended Metric         │
    ├────────────────────────────────────────────────────────────┤
    │  CI/CD automated tests       │  response_match_score       │
    │  Quick regression checks     │  response_match_score       │
    │  Quality assessment          │  final_response_match_v2    │
    │  Flexible output formats     │  final_response_match_v2    │
    │  Multiple valid answers      │  final_response_match_v2    │
    └────────────────────────────────────────────────────────────┘
    """)


# =============================================================================
# Part 2: ROUGE-1 Scoring (Manual Implementation)
# =============================================================================

def calculate_rouge1_score(reference: str, candidate: str) -> dict:
    """
    Calculate ROUGE-1 score (word overlap).

    ROUGE-1 measures unigram (single word) overlap between:
    - Reference: The expected response
    - Candidate: The actual response

    Returns precision, recall, and F1 score.
    """
    # Tokenize (simple word split)
    ref_words = set(reference.lower().split())
    cand_words = set(candidate.lower().split())

    # Calculate overlap
    overlap = ref_words.intersection(cand_words)

    # Precision: What % of candidate words are in reference?
    precision = len(overlap) / len(cand_words) if cand_words else 0

    # Recall: What % of reference words are in candidate?
    recall = len(overlap) / len(ref_words) if ref_words else 0

    # F1: Harmonic mean of precision and recall
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "overlap_words": list(overlap),
    }


def demo_rouge_scoring():
    """Demonstrate ROUGE-1 scoring with examples."""
    print("\n  ROUGE-1 Scoring Examples:")
    print("  " + "-"*50)

    examples = [
        # (reference, candidate, description)
        (
            "The result is 42",
            "The result is 42",
            "Exact match"
        ),
        (
            "The result is 42",
            "42 is the result",
            "Same words, different order"
        ),
        (
            "The temperature is 72 degrees Fahrenheit",
            "It's 72°F outside",
            "Same meaning, different words"
        ),
        (
            "The capital of France is Paris",
            "Paris is the capital city of France",
            "Paraphrase with extra words"
        ),
        (
            "Error: Division by zero",
            "Cannot divide by zero",
            "Different wording, same concept"
        ),
    ]

    for ref, cand, desc in examples:
        scores = calculate_rouge1_score(ref, cand)
        print(f"\n  {desc}:")
        print(f"    Reference: '{ref}'")
        print(f"    Candidate: '{cand}'")
        print(f"    F1 Score: {scores['f1']} (threshold typically 0.8)")
        print(f"    Overlap: {scores['overlap_words']}")


# =============================================================================
# Part 3: Semantic Matching Concepts
# =============================================================================

def explain_semantic_matching():
    """Explain LLM-as-judge semantic matching."""
    print("""
    SEMANTIC MATCHING (final_response_match_v2)
    ============================================

    Uses an LLM to judge if two responses mean the same thing.

    HOW IT WORKS:
    -------------
    1. Send both responses to a judge LLM
    2. Ask: "Do these responses convey the same information?"
    3. Judge returns: VALID or INVALID
    4. Repeat multiple times (num_samples) for robustness
    5. Use majority vote for final decision

    CONFIGURATION:
    --------------
    {
      "criteria": {
        "final_response_match_v2": {
          "threshold": 0.8,
          "judge_model_options": {
            "judge_model": "gemini-2.5-flash",
            "num_samples": 5
          }
        }
      }
    }

    WHAT THE JUDGE CONSIDERS:
    -------------------------
    ✓ Same core information
    ✓ Different phrasing is OK
    ✓ Additional correct details are OK
    ✗ Missing key information
    ✗ Contradictory statements
    ✗ Factually incorrect additions

    EXAMPLES:
    ---------
    Reference: "The sum of 5 and 3 is 8"
    Candidate: "5 + 3 = 8"
    Result: VALID (same meaning)

    Reference: "The capital of France is Paris"
    Candidate: "Paris, located in France, is the capital"
    Result: VALID (same info + extra correct detail)

    Reference: "The result is 42"
    Candidate: "The result is 24"
    Result: INVALID (contradictory)
    """)


# =============================================================================
# Part 4: Sample Agent for Response Testing
# =============================================================================

def get_weather(city: str) -> dict:
    """Get weather for a city (simulated)."""
    weather_data = {
        "new york": {"temp": 72, "condition": "sunny", "humidity": 45},
        "london": {"temp": 55, "condition": "cloudy", "humidity": 80},
        "tokyo": {"temp": 68, "condition": "rainy", "humidity": 90},
    }
    return weather_data.get(city.lower(), {"error": "City not found"})


def create_weather_agent():
    """Create a weather agent for response evaluation testing."""
    weather_tool = FunctionTool(func=get_weather)

    agent = LlmAgent(
        name="WeatherAgent",
        model="gemini-2.0-flash",
        instruction="""You are a weather assistant.
        When asked about weather, use the get_weather tool.
        Report the temperature, conditions, and humidity.
        Be concise but include all three pieces of information.""",
        tools=[weather_tool],
    )

    return agent


async def run_response_evaluation_demo():
    """Run agent and show response for evaluation analysis."""
    print("\n  Running weather agent to generate responses...")

    agent = create_weather_agent()
    session_service = InMemorySessionService()

    runner = Runner(
        agent=agent,
        app_name="weather_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="weather_demo",
        user_id="user1",
        session_id="weather_session",
        state={}
    )

    # Test query
    queries = [
        "What's the weather in New York?",
        "How's the weather in London today?",
    ]

    responses = []

    for query in queries:
        print(f"\n  Query: '{query}'")

        user_message = types.Content(parts=[types.Part(text=query)])

        async for event in runner.run_async(
            user_id="user1",
            session_id="weather_session",
            new_message=user_message,
        ):
            if event.is_final_response() and event.content:
                response = event.content.parts[0].text
                responses.append({"query": query, "response": response})
                print(f"  Response: {response[:120]}...")

    return responses


# =============================================================================
# Part 5: Response Evaluation Simulation
# =============================================================================

def simulate_response_evaluation(actual_responses: list):
    """Simulate response evaluation with different reference responses."""
    print("\n  Simulating evaluation against reference responses:")
    print("  " + "-"*50)

    # Reference responses (what we expect)
    references = {
        "What's the weather in New York?": [
            "It's 72°F and sunny in New York with 45% humidity.",
            "New York: Temperature 72°F, Sunny, Humidity 45%",
            "The weather in New York is sunny with a temperature of 72 degrees and humidity at 45 percent.",
        ],
        "How's the weather in London today?": [
            "London is cloudy at 55°F with 80% humidity.",
            "It's 55 degrees and cloudy in London, humidity is 80%.",
        ],
    }

    for response_data in actual_responses:
        query = response_data["query"]
        actual = response_data["response"]

        print(f"\n  Query: {query}")
        print(f"  Actual response: {actual[:80]}...")

        if query in references:
            for i, ref in enumerate(references[query], 1):
                score = calculate_rouge1_score(ref, actual)
                status = "PASS" if score['f1'] >= 0.5 else "NEEDS_SEMANTIC"
                print(f"    vs Reference {i}: ROUGE-1 F1={score['f1']:.2f} [{status}]")


# =============================================================================
# Part 6: Best Practices
# =============================================================================

def show_best_practices():
    """Show best practices for response evaluation."""
    print("""
    RESPONSE EVALUATION BEST PRACTICES
    ===================================

    1. CHOOSE THE RIGHT METRIC:
       -------------------------
       - Use response_match_score for quick, deterministic checks
       - Use final_response_match_v2 when meaning matters more than words

    2. SET APPROPRIATE THRESHOLDS:
       ----------------------------
       - 1.0 = Perfect match (too strict for most cases)
       - 0.8 = Good match (recommended default)
       - 0.6 = Moderate match (for flexible outputs)

    3. WRITE GOOD REFERENCE RESPONSES:
       ---------------------------------
       - Include the core information
       - Don't be overly specific about phrasing
       - Consider multiple valid phrasings

    4. HANDLE VARIABILITY:
       --------------------
       # Multiple runs to account for LLM variability
       AgentEvaluator.evaluate(
           agent_module="my_agent",
           eval_dataset_file_path_or_dir="tests/",
           num_runs=3,  # Run each test 3 times
       )

    5. COMBINE METRICS:
       -----------------
       {
         "criteria": {
           "response_match_score": 0.6,           // Baseline word overlap
           "final_response_match_v2": {           // Semantic check
             "threshold": 0.8
           }
         }
       }

    6. TEST FILE ORGANIZATION:
       ------------------------
       my_agent/
       ├── agent.py                  # Agent definition
       ├── test_config.json          # Evaluation criteria
       └── tests/
           ├── basic.test.json       # Basic functionality
           ├── edge_cases.test.json  # Edge cases
           └── multi_turn.test.json  # Multi-turn conversations
    """)


async def main():
    print("\n" + "#"*70)
    print("# Lab 5 Exercise 2: Response Evaluation")
    print("#"*70)

    # =========================================================================
    # Part 1: Overview
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: Understanding Response Evaluation")
    print("="*60)
    explain_response_evaluation()

    # =========================================================================
    # Part 2: ROUGE-1 Scoring
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: ROUGE-1 Word Overlap Scoring")
    print("="*60)
    demo_rouge_scoring()

    # =========================================================================
    # Part 3: Semantic Matching
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: Semantic Matching with LLM-as-Judge")
    print("="*60)
    explain_semantic_matching()

    # =========================================================================
    # Part 4: Running Agent
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Running Weather Agent")
    print("="*60)

    responses = await run_response_evaluation_demo()

    # =========================================================================
    # Part 5: Evaluation Simulation
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: Response Evaluation Simulation")
    print("="*60)

    simulate_response_evaluation(responses)

    # =========================================================================
    # Part 6: Best Practices
    # =========================================================================
    print("\n" + "="*60)
    print("PART 6: Best Practices")
    print("="*60)
    show_best_practices()

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Response Evaluation")
    print("#"*70)
    print("""
    RESPONSE EVALUATION METRICS:
    ----------------------------

    1. response_match_score (ROUGE-1)
       - Measures word overlap
       - Fast and deterministic
       - Best for CI/CD and regression testing
       - Config: {"response_match_score": 0.8}

    2. final_response_match_v2 (LLM-as-Judge)
       - Measures semantic similarity
       - Understands meaning, not just words
       - Best for quality assessment
       - Config:
         {
           "final_response_match_v2": {
             "threshold": 0.8,
             "judge_model_options": {
               "judge_model": "gemini-2.5-flash",
               "num_samples": 5
             }
           }
         }

    KEY TAKEAWAYS:
    --------------
    - ROUGE-1 is fast but misses semantic similarity
    - LLM-as-judge is slower but understands meaning
    - Use appropriate thresholds (0.8 is a good default)
    - Combine both for comprehensive evaluation
    - Write reference responses with core info, not exact phrasing
    """)


if __name__ == "__main__":
    asyncio.run(main())
