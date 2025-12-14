"""
Lab 4 - Exercise 4: Multi-Agent Patterns
=========================================

This exercise demonstrates common multi-agent orchestration patterns:
1. Coordinator/Dispatcher pattern
2. Generator-Critic pattern
3. Pipeline pattern
4. Fan-Out/Gather pattern
5. Hierarchical decomposition

Run: uv run python 04_agent_patterns.py
"""

import asyncio
from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent, BaseAgent
from google.adk.tools import agent_tool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.events import Event, EventActions
from google.genai import types
from typing import AsyncGenerator


# =============================================================================
# Pattern 1: Coordinator/Dispatcher
# =============================================================================

def create_coordinator_pattern():
    """
    Coordinator pattern: Central agent routes to specialists.

    Use case: Customer service, help desks, multi-domain assistants
    """

    # Specialist agents
    finance_expert = LlmAgent(
        name="FinanceExpert",
        model="gemini-2.0-flash",
        description="Handles financial questions: budgets, investments, taxes, savings.",
        instruction="""You are a finance expert.
        Provide clear, helpful advice on financial matters.
        Keep responses under 50 words.""",
    )

    health_expert = LlmAgent(
        name="HealthExpert",
        model="gemini-2.0-flash",
        description="Handles health questions: nutrition, exercise, wellness, symptoms.",
        instruction="""You are a health advisor.
        Provide general wellness guidance.
        Always recommend consulting a doctor for medical issues.
        Keep responses under 50 words.""",
    )

    tech_expert = LlmAgent(
        name="TechExpert",
        model="gemini-2.0-flash",
        description="Handles technology questions: programming, gadgets, software, IT.",
        instruction="""You are a tech expert.
        Help with technology-related questions.
        Keep responses under 50 words.""",
    )

    # Coordinator
    coordinator = LlmAgent(
        name="ExpertCoordinator",
        model="gemini-2.0-flash",
        description="Routes questions to the appropriate expert.",
        instruction="""You are a coordinator with access to experts:
        - FinanceExpert: money, budgets, investments
        - HealthExpert: health, fitness, nutrition
        - TechExpert: technology, programming, gadgets

        Analyze the user's question and transfer to the right expert.
        If unsure, ask for clarification.""",
        sub_agents=[finance_expert, health_expert, tech_expert],
    )

    return coordinator


# =============================================================================
# Pattern 2: Generator-Critic (Writer-Reviewer)
# =============================================================================

def create_generator_critic_pattern():
    """
    Generator-Critic pattern: One agent creates, another critiques.

    Use case: Content review, code review, quality assurance
    """

    # Generator: Creates initial content
    generator = LlmAgent(
        name="ContentGenerator",
        model="gemini-2.0-flash",
        instruction="""You are a content writer.
        Write a short paragraph (2-3 sentences) about the given topic.
        Make it informative but engaging.""",
        output_key="draft",
    )

    # Critic: Reviews and provides feedback
    critic = LlmAgent(
        name="ContentCritic",
        model="gemini-2.0-flash",
        instruction="""You are a content critic.
        Review this draft: {draft}

        Provide specific feedback:
        1. What's good about it?
        2. What could be improved?
        Keep feedback concise (2-3 points each).""",
        output_key="critique",
    )

    # Improver: Takes feedback and improves
    improver = LlmAgent(
        name="ContentImprover",
        model="gemini-2.0-flash",
        instruction="""You are a content editor.
        Original draft: {draft}
        Critique: {critique}

        Rewrite the content addressing the feedback.
        Output only the improved version.""",
    )

    pipeline = SequentialAgent(
        name="GeneratorCriticPipeline",
        sub_agents=[generator, critic, improver],
    )

    return pipeline


# =============================================================================
# Pattern 3: Pipeline Pattern
# =============================================================================

def create_pipeline_pattern():
    """
    Pipeline pattern: Data flows through transformation stages.

    Use case: ETL, document processing, data enrichment
    """

    # Stage 1: Extract
    extractor = LlmAgent(
        name="Extractor",
        model="gemini-2.0-flash",
        instruction="""Extract the key information from the input.
        Output as: Key points: [bullet points]""",
        output_key="extracted",
    )

    # Stage 2: Transform
    transformer = LlmAgent(
        name="Transformer",
        model="gemini-2.0-flash",
        instruction="""Transform this data: {extracted}

        Convert to a structured format:
        - Main topic:
        - Key details:
        - Category:""",
        output_key="transformed",
    )

    # Stage 3: Load/Format
    formatter = LlmAgent(
        name="Formatter",
        model="gemini-2.0-flash",
        instruction="""Format this structured data: {transformed}

        Create a nicely formatted summary with a title.""",
    )

    pipeline = SequentialAgent(
        name="ETLPipeline",
        sub_agents=[extractor, transformer, formatter],
    )

    return pipeline


# =============================================================================
# Pattern 4: Fan-Out/Gather Pattern
# =============================================================================

def create_fan_out_gather_pattern():
    """
    Fan-Out/Gather: Distribute work, then combine results.

    Use case: Parallel research, multi-source data gathering
    """

    # Fan-out: Multiple parallel agents
    researcher1 = LlmAgent(
        name="TechResearcher",
        model="gemini-2.0-flash",
        instruction="""You research technology trends.
        Provide one key insight about AI in 2024.
        Keep it to one sentence.""",
        output_key="tech_insight",
    )

    researcher2 = LlmAgent(
        name="BusinessResearcher",
        model="gemini-2.0-flash",
        instruction="""You research business trends.
        Provide one key insight about remote work in 2024.
        Keep it to one sentence.""",
        output_key="business_insight",
    )

    researcher3 = LlmAgent(
        name="SocialResearcher",
        model="gemini-2.0-flash",
        instruction="""You research social trends.
        Provide one key insight about social media in 2024.
        Keep it to one sentence.""",
        output_key="social_insight",
    )

    # Fan-out stage
    fan_out = ParallelAgent(
        name="ParallelResearch",
        sub_agents=[researcher1, researcher2, researcher3],
    )

    # Gather: Combine all results
    gatherer = LlmAgent(
        name="InsightGatherer",
        model="gemini-2.0-flash",
        instruction="""Combine these insights into a cohesive summary:

        Tech: {tech_insight}
        Business: {business_insight}
        Social: {social_insight}

        Write a brief paragraph connecting all three trends.""",
    )

    # Full workflow
    workflow = SequentialAgent(
        name="FanOutGather",
        sub_agents=[fan_out, gatherer],
    )

    return workflow


# =============================================================================
# Pattern 5: Hierarchical Decomposition
# =============================================================================

def create_hierarchical_pattern():
    """
    Hierarchical pattern: Break complex tasks into subtasks.

    Use case: Complex projects, report generation, research
    """

    # Level 2: Specialist tools (wrapped as AgentTools)
    fact_finder = LlmAgent(
        name="FactFinder",
        model="gemini-2.0-flash",
        instruction="""Find key facts about the given topic.
        Output 2-3 bullet points.""",
    )

    example_generator = LlmAgent(
        name="ExampleGenerator",
        model="gemini-2.0-flash",
        instruction="""Generate a practical example for the topic.
        Keep it brief and illustrative.""",
    )

    # Wrap as tools
    fact_tool = agent_tool.AgentTool(agent=fact_finder)
    example_tool = agent_tool.AgentTool(agent=example_generator)

    # Level 1: Research coordinator uses specialist tools
    research_coordinator = LlmAgent(
        name="ResearchCoordinator",
        model="gemini-2.0-flash",
        instruction="""You coordinate research on topics.

        For each topic:
        1. Use FactFinder to get key facts
        2. Use ExampleGenerator to get examples

        Combine results into a brief research summary.""",
        tools=[fact_tool, example_tool],
        output_key="research_results",
    )

    # Level 0: Report writer uses research results
    report_writer = LlmAgent(
        name="ReportWriter",
        model="gemini-2.0-flash",
        instruction="""Write a brief report using this research: {research_results}

        Format:
        # Topic Report
        ## Key Findings
        [findings]
        ## Example
        [example]
        ## Conclusion
        [brief conclusion]""",
    )

    workflow = SequentialAgent(
        name="HierarchicalResearch",
        sub_agents=[research_coordinator, report_writer],
    )

    return workflow


async def main():
    print("\n" + "#"*70)
    print("# Lab 4 Exercise 4: Multi-Agent Patterns")
    print("#"*70)

    session_service = InMemorySessionService()

    # =========================================================================
    # Pattern 1: Coordinator/Dispatcher
    # =========================================================================
    print("\n" + "="*60)
    print("PATTERN 1: Coordinator/Dispatcher")
    print("="*60)
    print("  Use case: Route requests to domain experts")

    coordinator = create_coordinator_pattern()

    runner1 = Runner(
        agent=coordinator,
        app_name="patterns_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="patterns_demo",
        user_id="user1",
        session_id="coordinator_session",
        state={}
    )

    test_questions = [
        ("Finance", "What's a good way to start investing?"),
        ("Health", "How much water should I drink daily?"),
        ("Tech", "What programming language should I learn first?"),
    ]

    for domain, question in test_questions:
        print(f"\n  [{domain}] Question: {question}")
        user_message = types.Content(parts=[types.Part(text=question)])

        async for event in runner1.run_async(
            user_id="user1",
            session_id="coordinator_session",
            new_message=user_message,
        ):
            if event.is_final_response() and event.content:
                print(f"  Response: {event.content.parts[0].text[:100]}...")

    # =========================================================================
    # Pattern 2: Generator-Critic
    # =========================================================================
    print("\n" + "="*60)
    print("PATTERN 2: Generator-Critic")
    print("="*60)
    print("  Use case: Content creation with review")

    gen_critic = create_generator_critic_pattern()

    runner2 = Runner(
        agent=gen_critic,
        app_name="patterns_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="patterns_demo",
        user_id="user1",
        session_id="gencritic_session",
        state={}
    )

    print("\n  Topic: 'The benefits of meditation'")
    user_message = types.Content(
        parts=[types.Part(text="The benefits of meditation")]
    )

    async for event in runner2.run_async(
        user_id="user1",
        session_id="gencritic_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"\n  Final (improved) content:\n  {event.content.parts[0].text[:200]}...")

    session = await session_service.get_session(
        app_name="patterns_demo",
        user_id="user1",
        session_id="gencritic_session"
    )

    print(f"\n  Original draft: {str(session.state.get('draft', ''))[:80]}...")
    print(f"  Critique: {str(session.state.get('critique', ''))[:80]}...")

    # =========================================================================
    # Pattern 3: Pipeline
    # =========================================================================
    print("\n" + "="*60)
    print("PATTERN 3: Pipeline (ETL)")
    print("="*60)
    print("  Use case: Data processing, document transformation")

    pipeline = create_pipeline_pattern()

    runner3 = Runner(
        agent=pipeline,
        app_name="patterns_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="patterns_demo",
        user_id="user1",
        session_id="pipeline_session",
        state={}
    )

    input_text = """
    Apple Inc. announced today that it will invest $1 billion in AI research.
    CEO Tim Cook said the investment will focus on machine learning and
    natural language processing. The company plans to hire 500 new researchers.
    """

    print(f"\n  Input: {input_text[:80]}...")
    user_message = types.Content(parts=[types.Part(text=input_text)])

    async for event in runner3.run_async(
        user_id="user1",
        session_id="pipeline_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"\n  Formatted output:\n  {event.content.parts[0].text[:200]}...")

    # =========================================================================
    # Pattern 4: Fan-Out/Gather
    # =========================================================================
    print("\n" + "="*60)
    print("PATTERN 4: Fan-Out/Gather")
    print("="*60)
    print("  Use case: Parallel research, multi-source gathering")

    fan_out = create_fan_out_gather_pattern()

    runner4 = Runner(
        agent=fan_out,
        app_name="patterns_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="patterns_demo",
        user_id="user1",
        session_id="fanout_session",
        state={}
    )

    print("\n  Task: Gather insights from 3 domains in parallel")
    user_message = types.Content(
        parts=[types.Part(text="What are the trends in 2024?")]
    )

    async for event in runner4.run_async(
        user_id="user1",
        session_id="fanout_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"\n  Combined insights:\n  {event.content.parts[0].text[:200]}...")

    session = await session_service.get_session(
        app_name="patterns_demo",
        user_id="user1",
        session_id="fanout_session"
    )

    print("\n  Individual insights (gathered in parallel):")
    print(f"    Tech: {session.state.get('tech_insight', 'N/A')[:60]}...")
    print(f"    Business: {session.state.get('business_insight', 'N/A')[:60]}...")
    print(f"    Social: {session.state.get('social_insight', 'N/A')[:60]}...")

    # =========================================================================
    # Pattern 5: Hierarchical Decomposition
    # =========================================================================
    print("\n" + "="*60)
    print("PATTERN 5: Hierarchical Decomposition")
    print("="*60)
    print("  Use case: Complex tasks broken into subtasks")

    hierarchical = create_hierarchical_pattern()

    runner5 = Runner(
        agent=hierarchical,
        app_name="patterns_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="patterns_demo",
        user_id="user1",
        session_id="hierarchical_session",
        state={}
    )

    print("\n  Topic: 'Machine Learning'")
    print("  Hierarchy: ReportWriter -> ResearchCoordinator -> [FactFinder, ExampleGenerator]")

    user_message = types.Content(
        parts=[types.Part(text="Machine Learning")]
    )

    async for event in runner5.run_async(
        user_id="user1",
        session_id="hierarchical_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"\n  Final report:\n  {event.content.parts[0].text[:300]}...")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Multi-Agent Patterns")
    print("#"*70)
    print("""
    PATTERN 1: COORDINATOR/DISPATCHER
    ---------------------------------
    coordinator = LlmAgent(
        name="Coordinator",
        sub_agents=[expert_a, expert_b, expert_c]
    )
    - Central routing based on request type
    - Use case: Customer service, help desks

    PATTERN 2: GENERATOR-CRITIC
    ---------------------------
    pipeline = SequentialAgent(
        sub_agents=[generator, critic, improver]
    )
    - Create -> Review -> Improve cycle
    - Use case: Content review, QA

    PATTERN 3: PIPELINE (ETL)
    -------------------------
    pipeline = SequentialAgent(
        sub_agents=[extractor, transformer, loader]
    )
    - Sequential data transformation
    - Use case: Document processing, data pipelines

    PATTERN 4: FAN-OUT/GATHER
    -------------------------
    workflow = SequentialAgent(sub_agents=[
        ParallelAgent(sub_agents=[a, b, c]),  # Fan-out
        gatherer  # Gather
    ])
    - Parallel work, then combine
    - Use case: Multi-source research

    PATTERN 5: HIERARCHICAL DECOMPOSITION
    -------------------------------------
    coordinator = LlmAgent(
        tools=[
            AgentTool(agent=specialist_a),
            AgentTool(agent=specialist_b)
        ]
    )
    - Break complex tasks into subtasks
    - Use case: Complex projects, research

    CHOOSING A PATTERN:
    -------------------
    | Need                    | Pattern              |
    |-------------------------|----------------------|
    | Route by domain         | Coordinator          |
    | Quality improvement     | Generator-Critic     |
    | Sequential processing   | Pipeline             |
    | Parallel work           | Fan-Out/Gather       |
    | Complex decomposition   | Hierarchical         |

    COMBINING PATTERNS:
    -------------------
    You can mix patterns! E.g.:
    - Coordinator with Pipeline sub-agents
    - Fan-Out with Generator-Critic at each branch
    - Hierarchical with Parallel at leaf level
    """)


if __name__ == "__main__":
    asyncio.run(main())
