"""
Lab 4 - Exercise 3: Agent Communication
========================================

This exercise demonstrates how agents share information:
1. State-based communication
2. AgentTool - using agents as callable tools
3. Data passing between agents
4. Explicit vs implicit invocation

Run: uv run python 03_agent_communication.py
"""

import asyncio
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import FunctionTool, agent_tool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# =============================================================================
# Part 1: State-Based Communication
# =============================================================================

def create_state_communication_demo():
    """
    Demonstrate communication through shared state.

    Agent A writes to state -> Agent B reads from state
    """

    # Agent A: Fetches data and saves to state
    data_fetcher = LlmAgent(
        name="DataFetcher",
        model="gemini-2.0-flash",
        instruction="""You are a data fetcher.
        When asked about a topic, provide 3 interesting facts.
        Format as a numbered list.""",
        output_key="fetched_data",  # Saves output to state['fetched_data']
    )

    # Agent B: Reads from state and processes
    data_processor = LlmAgent(
        name="DataProcessor",
        model="gemini-2.0-flash",
        instruction="""You are a data processor.
        You have access to this data: {fetched_data}

        Summarize the data into one concise sentence.
        Start with "Summary:".""",
        output_key="processed_data",
    )

    # Agent C: Uses processed data
    reporter = LlmAgent(
        name="Reporter",
        model="gemini-2.0-flash",
        instruction="""You are a reporter.
        Original data: {fetched_data}
        Summary: {processed_data}

        Create a brief report with a title and the summary.""",
    )

    # Sequential pipeline with state sharing
    pipeline = SequentialAgent(
        name="DataPipeline",
        sub_agents=[data_fetcher, data_processor, reporter],
    )

    return pipeline


# =============================================================================
# Part 2: AgentTool - Agent as a Callable Tool
# =============================================================================

def create_agent_tool_demo():
    """
    Demonstrate using an agent as a tool.

    MainAgent can explicitly call HelperAgent as a tool.
    """

    # Helper agent that does calculations
    calculator_agent = LlmAgent(
        name="CalculatorAgent",
        model="gemini-2.0-flash",
        instruction="""You are a calculator.
        Given a math expression, compute the result.
        Output ONLY the numeric result, nothing else.""",
    )

    # Helper agent that translates
    translator_agent = LlmAgent(
        name="TranslatorAgent",
        model="gemini-2.0-flash",
        instruction="""You are a translator.
        Translate the given text to Spanish.
        Output ONLY the translation, nothing else.""",
    )

    # Wrap agents as tools
    calc_tool = agent_tool.AgentTool(agent=calculator_agent)
    translate_tool = agent_tool.AgentTool(agent=translator_agent)

    # Main agent that uses the helper agents as tools
    main_agent = LlmAgent(
        name="MainAssistant",
        model="gemini-2.0-flash",
        instruction="""You are a helpful assistant with access to specialized tools.

        You have two tools:
        1. CalculatorAgent - Use for any math calculations
        2. TranslatorAgent - Use to translate text to Spanish

        When the user needs math, use CalculatorAgent.
        When the user needs translation, use TranslatorAgent.

        Explain what you're doing and provide the result.""",
        tools=[calc_tool, translate_tool],
    )

    return main_agent


# =============================================================================
# Part 3: Data Flow Patterns
# =============================================================================

def create_data_flow_demo():
    """
    Complex data flow between multiple agents.
    """

    # Agent that extracts entities
    entity_extractor = LlmAgent(
        name="EntityExtractor",
        model="gemini-2.0-flash",
        instruction="""Extract named entities (people, places, organizations) from:
        {user_input}

        Output as a comma-separated list.""",
        output_key="entities",
    )

    # Agent that categorizes
    categorizer = LlmAgent(
        name="Categorizer",
        model="gemini-2.0-flash",
        instruction="""Given these entities: {entities}

        Categorize each as Person, Place, or Organization.
        Format: Entity (Category)""",
        output_key="categorized",
    )

    # Agent that generates summary
    summary_generator = LlmAgent(
        name="SummaryGenerator",
        model="gemini-2.0-flash",
        instruction="""Original input: {user_input}
        Entities found: {entities}
        Categorized: {categorized}

        Write a one-sentence summary mentioning the key entities.""",
    )

    pipeline = SequentialAgent(
        name="EntityPipeline",
        sub_agents=[entity_extractor, categorizer, summary_generator],
    )

    return pipeline


# =============================================================================
# Part 4: Combining State and Tools
# =============================================================================

def create_combined_demo():
    """
    Demonstrate both state communication and tool-based communication.
    """

    # A simple tool that the agent can use
    def lookup_info(topic: str) -> dict:
        """Look up information about a topic."""
        # Simulated database
        data = {
            "python": "Python is a programming language created by Guido van Rossum.",
            "ai": "AI stands for Artificial Intelligence, the simulation of human intelligence.",
            "default": f"Information about {topic} is not in the database."
        }
        return {"result": data.get(topic.lower(), data["default"])}

    lookup_tool = FunctionTool(func=lookup_info)

    # First agent: uses tool to gather info
    info_gatherer = LlmAgent(
        name="InfoGatherer",
        model="gemini-2.0-flash",
        instruction="""You gather information about topics.
        Use the lookup_info tool to find information.
        After looking up, report what you found.""",
        tools=[lookup_tool],
        output_key="gathered_info",
    )

    # Second agent: processes the gathered info
    processor = LlmAgent(
        name="InfoProcessor",
        model="gemini-2.0-flash",
        instruction="""Process this information: {gathered_info}

        Rephrase it in a more engaging way.
        Add an interesting follow-up fact.""",
    )

    pipeline = SequentialAgent(
        name="InfoPipeline",
        sub_agents=[info_gatherer, processor],
    )

    return pipeline


async def main():
    print("\n" + "#"*70)
    print("# Lab 4 Exercise 3: Agent Communication")
    print("#"*70)

    session_service = InMemorySessionService()

    # =========================================================================
    # Part 1: State-Based Communication
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: State-Based Communication")
    print("="*60)
    print("  DataFetcher -> state -> DataProcessor -> state -> Reporter")

    pipeline1 = create_state_communication_demo()

    runner1 = Runner(
        agent=pipeline1,
        app_name="comm_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="comm_demo",
        user_id="user1",
        session_id="state_session",
        state={}
    )

    print("\n  Input: 'Tell me about space exploration'")
    user_message = types.Content(
        parts=[types.Part(text="Tell me about space exploration")]
    )

    async for event in runner1.run_async(
        user_id="user1",
        session_id="state_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"\n  Final Report:\n  {event.content.parts[0].text[:200]}...")

    session = await session_service.get_session(
        app_name="comm_demo",
        user_id="user1",
        session_id="state_session"
    )

    print("\n  State contents after pipeline:")
    print(f"    fetched_data: {str(session.state.get('fetched_data', ''))[:80]}...")
    print(f"    processed_data: {str(session.state.get('processed_data', ''))[:80]}...")

    # =========================================================================
    # Part 2: AgentTool
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: AgentTool - Agents as Callable Tools")
    print("="*60)
    print("  MainAssistant has CalculatorAgent and TranslatorAgent as tools")

    main_agent = create_agent_tool_demo()

    runner2 = Runner(
        agent=main_agent,
        app_name="comm_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="comm_demo",
        user_id="user1",
        session_id="tool_session",
        state={}
    )

    # Test calculation
    print("\n  Test 1: Math calculation")
    print("  Input: 'What is 25 * 17?'")
    user_message = types.Content(
        parts=[types.Part(text="What is 25 * 17?")]
    )

    async for event in runner2.run_async(
        user_id="user1",
        session_id="tool_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text[:150]}...")

    # Test translation
    print("\n  Test 2: Translation")
    print("  Input: 'Translate \"Hello, how are you?\" to Spanish'")
    user_message = types.Content(
        parts=[types.Part(text='Translate "Hello, how are you?" to Spanish')]
    )

    async for event in runner2.run_async(
        user_id="user1",
        session_id="tool_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text[:150]}...")

    # =========================================================================
    # Part 3: Complex Data Flow
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: Complex Data Flow")
    print("="*60)
    print("  Extract entities -> Categorize -> Generate summary")

    pipeline3 = create_data_flow_demo()

    runner3 = Runner(
        agent=pipeline3,
        app_name="comm_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="comm_demo",
        user_id="user1",
        session_id="flow_session",
        state={"user_input": "Elon Musk announced that SpaceX will launch from Cape Canaveral next month."}
    )

    print("\n  Input: 'Elon Musk announced that SpaceX will launch from Cape Canaveral...'")
    user_message = types.Content(
        parts=[types.Part(text="Process this")]
    )

    async for event in runner3.run_async(
        user_id="user1",
        session_id="flow_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"\n  Final output: {event.content.parts[0].text[:150]}...")

    session = await session_service.get_session(
        app_name="comm_demo",
        user_id="user1",
        session_id="flow_session"
    )

    print("\n  Data flow through state:")
    print(f"    entities: {session.state.get('entities', 'N/A')[:60]}...")
    print(f"    categorized: {session.state.get('categorized', 'N/A')[:60]}...")

    # =========================================================================
    # Part 4: State + Tools Combined
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Combining State and Tools")
    print("="*60)
    print("  Agent uses tool, saves to state, next agent processes")

    pipeline4 = create_combined_demo()

    runner4 = Runner(
        agent=pipeline4,
        app_name="comm_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="comm_demo",
        user_id="user1",
        session_id="combined_session",
        state={}
    )

    print("\n  Input: 'Tell me about Python'")
    user_message = types.Content(
        parts=[types.Part(text="Tell me about Python")]
    )

    async for event in runner4.run_async(
        user_id="user1",
        session_id="combined_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"\n  Final output: {event.content.parts[0].text[:200]}...")

    # =========================================================================
    # Part 5: Comparison
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: State vs AgentTool - When to Use Each")
    print("="*60)

    print("""
    STATE-BASED COMMUNICATION:
    --------------------------
    # Agent A saves to state
    agent_a = LlmAgent(
        name="AgentA",
        output_key="result_a"  # Saves output to state['result_a']
    )

    # Agent B reads from state
    agent_b = LlmAgent(
        name="AgentB",
        instruction="Process {result_a}"  # Reads state['result_a']
    )

    WHEN TO USE:
    - Sequential pipelines
    - Data flows through multiple stages
    - Agents run one after another
    - No complex control flow needed

    AGENT TOOL:
    -----------
    # Wrap agent as a tool
    helper_tool = agent_tool.AgentTool(agent=helper_agent)

    # Parent uses it as a tool
    parent = LlmAgent(
        name="Parent",
        tools=[helper_tool]
    )

    WHEN TO USE:
    - Parent needs to decide WHEN to call child
    - Multiple calls might be needed
    - Parent processes the result further
    - More complex control flow

    COMPARISON:
    -----------
    | Aspect         | State-Based      | AgentTool         |
    |----------------|------------------|-------------------|
    | Control        | Sequential       | LLM-driven        |
    | Invocation     | Automatic        | Explicit          |
    | Data access    | Via {key}        | Tool returns      |
    | Flexibility    | Fixed order      | Dynamic           |
    | Use case       | Pipelines        | Helper agents     |
    """)

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Agent Communication")
    print("#"*70)
    print("""
    STATE-BASED COMMUNICATION:
    --------------------------
    1. Agent saves output with output_key
       agent = LlmAgent(output_key="my_data")

    2. Next agent accesses via template
       agent = LlmAgent(instruction="Use {my_data}")

    3. State persists through session
       session.state['my_data'] contains the value

    AGENT TOOL:
    -----------
    from google.adk.tools import agent_tool

    # Wrap any agent as a tool
    helper_tool = agent_tool.AgentTool(agent=helper_agent)

    # Use in another agent
    parent = LlmAgent(tools=[helper_tool])

    # Parent's LLM calls: HelperAgent(input="...")
    # Returns result to parent for further processing

    COMBINING PATTERNS:
    -------------------
    - Use state for pipeline data flow
    - Use AgentTool for dynamic helper calls
    - Mix both for complex workflows

    BEST PRACTICES:
    ---------------
    1. Use descriptive output_key names
    2. Document state keys in instructions
    3. Keep AgentTools focused and simple
    4. Test data flow at each stage
    5. Log intermediate state for debugging
    """)


if __name__ == "__main__":
    asyncio.run(main())
