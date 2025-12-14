"""
Lab 4 - Exercise 2: Workflow Agents
====================================

This exercise demonstrates built-in orchestration agents:
1. SequentialAgent - step-by-step execution
2. ParallelAgent - concurrent execution
3. LoopAgent - iterative refinement
4. output_key for data passing

Run: uv run python 02_workflow_agents.py
"""

import asyncio
from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent, LoopAgent, BaseAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.events import Event, EventActions
from google.genai import types
from typing import AsyncGenerator


# =============================================================================
# Part 1: SequentialAgent - Step by Step
# =============================================================================

def create_content_pipeline():
    """
    Create a content generation pipeline using SequentialAgent.

    Pipeline: Research -> Draft -> Review -> Format
    """

    # Step 1: Research the topic
    researcher = LlmAgent(
        name="Researcher",
        model="gemini-2.0-flash",
        instruction="""You are a researcher. Given a topic, provide 3 key facts.
        Format: Bullet points, one fact per line.
        Keep it brief (under 100 words).""",
        output_key="research_facts",  # Saves output to state['research_facts']
    )

    # Step 2: Draft content based on research
    drafter = LlmAgent(
        name="Drafter",
        model="gemini-2.0-flash",
        instruction="""You are a content writer.
        Using these research facts: {research_facts}

        Write a short paragraph (2-3 sentences) incorporating the facts.
        Keep it informative and engaging.""",
        output_key="draft_content",
    )

    # Step 3: Review and improve
    reviewer = LlmAgent(
        name="Reviewer",
        model="gemini-2.0-flash",
        instruction="""You are an editor.
        Review this draft: {draft_content}

        Improve clarity and fix any issues.
        Keep it concise. Output only the improved version.""",
        output_key="reviewed_content",
    )

    # Step 4: Final formatting
    formatter = LlmAgent(
        name="Formatter",
        model="gemini-2.0-flash",
        instruction="""You are a formatter.
        Take this content: {reviewed_content}

        Add a catchy title and format nicely.
        Output the final formatted content.""",
    )

    # Sequential pipeline
    pipeline = SequentialAgent(
        name="ContentPipeline",
        sub_agents=[researcher, drafter, reviewer, formatter],
    )

    return pipeline


# =============================================================================
# Part 2: ParallelAgent - Concurrent Execution
# =============================================================================

def create_info_gatherer():
    """
    Create parallel information gatherer.

    Gathers: Weather summary, News summary, Quote of the day
    All at once!
    """

    weather_agent = LlmAgent(
        name="WeatherAgent",
        model="gemini-2.0-flash",
        instruction="""Provide a brief fictional weather update for New York City.
        Format: City, Temperature, Conditions (1 line).""",
        output_key="weather_info",
    )

    news_agent = LlmAgent(
        name="NewsAgent",
        model="gemini-2.0-flash",
        instruction="""Provide a brief fictional tech news headline.
        Format: One sentence headline.""",
        output_key="news_info",
    )

    quote_agent = LlmAgent(
        name="QuoteAgent",
        model="gemini-2.0-flash",
        instruction="""Provide an inspirational quote about technology.
        Format: "Quote" - Author""",
        output_key="quote_info",
    )

    # Parallel execution
    gatherer = ParallelAgent(
        name="InfoGatherer",
        sub_agents=[weather_agent, news_agent, quote_agent],
    )

    return gatherer


# =============================================================================
# Part 3: LoopAgent - Iterative Refinement
# =============================================================================

class QualityChecker(BaseAgent):
    """
    Custom agent that checks quality and decides whether to continue looping.
    Uses escalate=True to exit the loop when quality is good.
    """

    async def _run_async_impl(self, ctx) -> AsyncGenerator[Event, None]:
        # Track iteration in state (since we can't use instance variables with Pydantic)
        iteration = ctx.session.state.get("_qc_iteration", 0) + 1
        ctx.session.state["_qc_iteration"] = iteration
        max_iterations = 3

        # Get the current code from state
        current_code = ctx.session.state.get("current_code", "")

        # Simple quality check: does it have all required elements?
        has_function = "def " in current_code
        has_docstring = '"""' in current_code or "'''" in current_code
        has_return = "return" in current_code

        quality_score = sum([has_function, has_docstring, has_return])
        is_good = quality_score >= 3 or iteration >= max_iterations

        status = "PASS" if is_good else "NEEDS_IMPROVEMENT"

        # Save status to state
        ctx.session.state["quality_status"] = status
        ctx.session.state["quality_score"] = quality_score
        ctx.session.state["iteration"] = iteration

        print(f"    [QualityChecker] Iteration {iteration}: score={quality_score}/3, status={status}")

        # Escalate (exit loop) if quality is good
        yield Event(
            author=self.name,
            content=types.Content(
                role="model",
                parts=[types.Part(text=f"Quality check: {status} (score: {quality_score}/3)")]
            ),
            actions=EventActions(escalate=is_good)
        )


def create_code_refiner():
    """
    Create a code refinement loop.

    Loop: Generate/Refine -> Check Quality -> (repeat if needed)
    """

    code_writer = LlmAgent(
        name="CodeWriter",
        model="gemini-2.0-flash",
        instruction="""You are a Python developer.
        Task: Write or improve a function based on requirements.

        Current requirements: {requirements}
        Previous code (if any): {current_code}
        Quality feedback: {quality_status}

        If quality_status is NEEDS_IMPROVEMENT, add what's missing:
        - Ensure there's a function definition (def)
        - Ensure there's a docstring
        - Ensure there's a return statement

        Output ONLY the Python code, no explanations.""",
        output_key="current_code",
    )

    quality_checker = QualityChecker(name="QualityChecker")

    # Loop until quality passes or max iterations
    refiner = LoopAgent(
        name="CodeRefiner",
        max_iterations=5,
        sub_agents=[code_writer, quality_checker],
    )

    return refiner


# =============================================================================
# Part 4: Combining Workflow Agents
# =============================================================================

def create_combined_workflow():
    """
    Combine Sequential and Parallel in one workflow.

    1. Parallel: Gather multiple pieces of info
    2. Sequential: Summarize and format
    """

    # Parallel gathering
    fact1 = LlmAgent(
        name="Fact1Agent",
        model="gemini-2.0-flash",
        instruction="Provide one interesting fact about Python programming.",
        output_key="fact1",
    )

    fact2 = LlmAgent(
        name="Fact2Agent",
        model="gemini-2.0-flash",
        instruction="Provide one interesting fact about machine learning.",
        output_key="fact2",
    )

    gatherer = ParallelAgent(
        name="FactGatherer",
        sub_agents=[fact1, fact2],
    )

    # Summarizer that uses gathered facts
    summarizer = LlmAgent(
        name="Summarizer",
        model="gemini-2.0-flash",
        instruction="""Combine these facts into one coherent sentence:
        Fact 1: {fact1}
        Fact 2: {fact2}

        Create a brief summary connecting both facts.""",
    )

    # Full workflow: gather in parallel, then summarize
    workflow = SequentialAgent(
        name="GatherAndSummarize",
        sub_agents=[gatherer, summarizer],
    )

    return workflow


async def main():
    print("\n" + "#"*70)
    print("# Lab 4 Exercise 2: Workflow Agents")
    print("#"*70)

    session_service = InMemorySessionService()

    # =========================================================================
    # Part 1: SequentialAgent
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: SequentialAgent - Content Pipeline")
    print("="*60)
    print("  Pipeline: Research -> Draft -> Review -> Format")

    pipeline = create_content_pipeline()

    runner1 = Runner(
        agent=pipeline,
        app_name="workflow_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="workflow_demo",
        user_id="user1",
        session_id="sequential_session",
        state={}
    )

    print("\n  Input: 'Tell me about artificial intelligence'")
    user_message = types.Content(
        parts=[types.Part(text="Tell me about artificial intelligence")]
    )

    print("\n  Pipeline execution:")
    async for event in runner1.run_async(
        user_id="user1",
        session_id="sequential_session",
        new_message=user_message,
    ):
        if hasattr(event, 'author') and event.content:
            text = ""
            if event.content.parts:
                text = getattr(event.content.parts[0], 'text', '')[:80] if event.content.parts else ""
            if text:
                print(f"    [{event.author}]: {text}...")

    # Show state after pipeline
    session = await session_service.get_session(
        app_name="workflow_demo",
        user_id="user1",
        session_id="sequential_session"
    )
    print("\n  State after pipeline:")
    for key in ["research_facts", "draft_content", "reviewed_content"]:
        value = session.state.get(key, "")
        if value:
            print(f"    {key}: {str(value)[:60]}...")

    # =========================================================================
    # Part 2: ParallelAgent
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: ParallelAgent - Concurrent Info Gathering")
    print("="*60)
    print("  Gathers: Weather, News, Quote - all at once!")

    gatherer = create_info_gatherer()

    runner2 = Runner(
        agent=gatherer,
        app_name="workflow_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="workflow_demo",
        user_id="user1",
        session_id="parallel_session",
        state={}
    )

    print("\n  Input: 'Get today's info'")
    user_message = types.Content(
        parts=[types.Part(text="Get today's info")]
    )

    async for event in runner2.run_async(
        user_id="user1",
        session_id="parallel_session",
        new_message=user_message,
    ):
        pass  # Just process events

    session = await session_service.get_session(
        app_name="workflow_demo",
        user_id="user1",
        session_id="parallel_session"
    )

    print("\n  Results gathered in parallel:")
    for key in ["weather_info", "news_info", "quote_info"]:
        value = session.state.get(key, "N/A")
        print(f"    {key}: {str(value)[:70]}...")

    # =========================================================================
    # Part 3: LoopAgent
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: LoopAgent - Iterative Code Refinement")
    print("="*60)
    print("  Loop: Write -> Check -> (repeat until quality passes)")

    refiner = create_code_refiner()

    runner3 = Runner(
        agent=refiner,
        app_name="workflow_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="workflow_demo",
        user_id="user1",
        session_id="loop_session",
        state={
            "requirements": "Write a function that calculates factorial",
            "current_code": "",
            "quality_status": "NEEDS_IMPROVEMENT",
        }
    )

    print("\n  Requirements: 'Write a function that calculates factorial'")
    print("  Quality criteria: has function def, docstring, return statement")
    print("\n  Refinement loop:")

    user_message = types.Content(
        parts=[types.Part(text="Start")]
    )

    async for event in runner3.run_async(
        user_id="user1",
        session_id="loop_session",
        new_message=user_message,
    ):
        pass  # Quality checker prints status

    session = await session_service.get_session(
        app_name="workflow_demo",
        user_id="user1",
        session_id="loop_session"
    )

    print(f"\n  Final code:")
    final_code = session.state.get("current_code", "N/A")
    print(f"    {final_code[:200]}...")
    print(f"\n  Final quality: {session.state.get('quality_status')}")
    print(f"  Iterations used: {session.state.get('iteration')}")

    # =========================================================================
    # Part 4: Combined Workflow
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Combined Workflow (Parallel + Sequential)")
    print("="*60)
    print("  1. Parallel: Gather facts")
    print("  2. Sequential: Summarize")

    workflow = create_combined_workflow()

    runner4 = Runner(
        agent=workflow,
        app_name="workflow_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="workflow_demo",
        user_id="user1",
        session_id="combined_session",
        state={}
    )

    user_message = types.Content(
        parts=[types.Part(text="Gather facts and summarize")]
    )

    print("\n  Executing combined workflow...")
    final_response = ""
    async for event in runner4.run_async(
        user_id="user1",
        session_id="combined_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            final_response = event.content.parts[0].text

    session = await session_service.get_session(
        app_name="workflow_demo",
        user_id="user1",
        session_id="combined_session"
    )

    print(f"\n  Fact 1: {session.state.get('fact1', 'N/A')[:60]}...")
    print(f"  Fact 2: {session.state.get('fact2', 'N/A')[:60]}...")
    print(f"\n  Combined summary: {final_response[:120]}...")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Workflow Agents")
    print("#"*70)
    print("""
    SEQUENTIAL AGENT:
    -----------------
    pipeline = SequentialAgent(
        name="Pipeline",
        sub_agents=[step1, step2, step3]
    )
    - Executes agents one after another
    - Each agent can read previous agent's output
    - Use output_key to save results to state
    - Access via {key_name} in instructions

    PARALLEL AGENT:
    ---------------
    gatherer = ParallelAgent(
        name="Gatherer",
        sub_agents=[agent_a, agent_b, agent_c]
    )
    - Executes ALL agents concurrently
    - Faster for independent tasks
    - All share the same state
    - Great for gathering multiple data sources

    LOOP AGENT:
    -----------
    loop = LoopAgent(
        name="Refiner",
        max_iterations=5,
        sub_agents=[worker, checker]
    )
    - Repeats until escalate=True or max_iterations
    - Use EventActions(escalate=True) to exit
    - Great for iterative refinement
    - Quality checking patterns

    OUTPUT_KEY:
    -----------
    agent = LlmAgent(
        name="Agent",
        instruction="...",
        output_key="my_result"  # Saves to state['my_result']
    )
    - Agent's output is saved to state
    - Other agents access via {my_result}
    - Essential for data flow between agents

    COMBINING WORKFLOWS:
    --------------------
    workflow = SequentialAgent(
        sub_agents=[
            ParallelAgent(sub_agents=[a, b]),  # Step 1: Gather
            LlmAgent(instruction="Process {a_output} and {b_output}")  # Step 2: Process
        ]
    )
    - Nest workflow agents for complex flows
    - Parallel within Sequential is common
    - Build sophisticated pipelines
    """)


if __name__ == "__main__":
    asyncio.run(main())
