"""
Lab 1 - Exercise 4: State in Agent Instructions
================================================

This exercise demonstrates how to use state in agent instructions:
1. {key} templating - Inject state values into instructions
2. output_key - Automatically save agent responses to state
3. InstructionProvider - Dynamic instructions with ReadonlyContext

Run: uv run python 04_state_in_instructions.py
"""

import asyncio
from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# =============================================================================
# Example 1: Simple {key} Templating
# =============================================================================
print("Creating Agent 1: Simple {key} Templating...")

# The {topic} placeholder will be replaced with state['topic']
simple_template_agent = LlmAgent(
    name="SimpleTemplateAgent",
    model="gemini-2.0-flash",
    instruction="""You are a creative writing assistant.
    Write a very short story (2-3 sentences) about a {animal} who loves {activity}.
    The story should have a {mood} mood."""
)


# =============================================================================
# Example 2: Optional Keys with {key?}
# =============================================================================
print("Creating Agent 2: Optional Keys with {key?}...")

# Using {key?} won't error if key is missing (just empty string)
optional_key_agent = LlmAgent(
    name="OptionalKeyAgent",
    model="gemini-2.0-flash",
    instruction="""You are a greeting assistant.
    User's name: {user_name?}
    User's title: {user_title?}

    If you know the user's name, greet them personally.
    If you don't know their name, use a friendly generic greeting.
    Keep your response to one sentence."""
)


# =============================================================================
# Example 3: output_key - Save Response to State
# =============================================================================
print("Creating Agent 3: output_key for saving responses...")

# The agent's final response will be saved to state['generated_poem']
poem_agent = LlmAgent(
    name="PoemAgent",
    model="gemini-2.0-flash",
    instruction="""Write a short haiku (3 lines) about {subject}.
    Only output the haiku, nothing else.""",
    output_key="generated_poem"  # Response saved to state['generated_poem']
)

# This agent reads from the state where the poem was saved
poetry_critic = LlmAgent(
    name="PoetryCritic",
    model="gemini-2.0-flash",
    instruction="""You are a poetry critic.
    Here is a haiku to review:

    {generated_poem}

    Provide a one-sentence critique of this haiku."""
)


# =============================================================================
# Example 4: InstructionProvider for Dynamic Instructions
# =============================================================================
print("Creating Agent 4: InstructionProvider...")

def dynamic_instruction_provider(context: ReadonlyContext) -> str:
    """
    An InstructionProvider receives ReadonlyContext and returns a string.

    Benefits:
    - Full control over instruction generation
    - Can use complex logic to build instructions
    - Access to state without automatic templating
    - Can include literal {braces} without escaping
    """
    user_level = context.state.get("user_level", "beginner")
    user_interests = context.state.get("user_interests", [])
    conversation_count = context.state.get("conversation_count", 0)

    # Build instruction based on state
    base_instruction = "You are a helpful coding tutor."

    # Customize based on user level
    if user_level == "beginner":
        level_instruction = "Use simple language and explain concepts step by step."
    elif user_level == "intermediate":
        level_instruction = "You can use technical terms but explain complex concepts."
    else:
        level_instruction = "Feel free to use advanced terminology and concepts."

    # Add interests if available
    if user_interests:
        interests_str = ", ".join(user_interests)
        interests_instruction = f"The user is interested in: {interests_str}."
    else:
        interests_instruction = ""

    # Add context about conversation history
    if conversation_count > 0:
        history_instruction = f"This is message #{conversation_count + 1} in the conversation."
    else:
        history_instruction = "This is the start of a new conversation."

    # Combine all parts
    full_instruction = f"""
{base_instruction}

{level_instruction}

{interests_instruction}

{history_instruction}

Keep your responses concise (2-3 sentences max).
"""
    return full_instruction


dynamic_agent = LlmAgent(
    name="DynamicTutor",
    model="gemini-2.0-flash",
    instruction=dynamic_instruction_provider  # Pass function, not string
)


# =============================================================================
# Main demonstration
# =============================================================================
async def main():
    print("\n" + "#"*70)
    print("# Lab 1 Exercise 4: State in Agent Instructions")
    print("#"*70)

    session_service = InMemorySessionService()

    # =========================================================================
    # Demo 1: Simple {key} Templating
    # =========================================================================
    print("\n" + "="*60)
    print("DEMO 1: Simple {key} Templating")
    print("="*60)

    runner1 = Runner(
        agent=simple_template_agent,
        app_name="template_demo",
        session_service=session_service,
    )

    # Create session with template values in state
    await session_service.create_session(
        app_name="template_demo",
        user_id="user1",
        session_id="demo1",
        state={
            "animal": "cat",
            "activity": "coding",
            "mood": "whimsical"
        }
    )

    print("\n  State: animal=cat, activity=coding, mood=whimsical")
    print("  Template: Write a story about a {animal} who loves {activity}...")

    user_message = types.Content(parts=[types.Part(text="Write me a story!")])
    async for event in runner1.run_async(
        user_id="user1", session_id="demo1", new_message=user_message
    ):
        if event.is_final_response() and event.content:
            print(f"\n  Response:\n  {event.content.parts[0].text}")

    # =========================================================================
    # Demo 2: Optional Keys with {key?}
    # =========================================================================
    print("\n" + "="*60)
    print("DEMO 2: Optional Keys with {key?}")
    print("="*60)

    runner2 = Runner(
        agent=optional_key_agent,
        app_name="template_demo",
        session_service=session_service,
    )

    # Session WITH user_name
    await session_service.create_session(
        app_name="template_demo",
        user_id="user2",
        session_id="demo2a",
        state={"user_name": "Alice", "user_title": "Dr."}
    )

    print("\n  Test A - With name: user_name=Alice, user_title=Dr.")
    user_message = types.Content(parts=[types.Part(text="Hello!")])
    async for event in runner2.run_async(
        user_id="user2", session_id="demo2a", new_message=user_message
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text}")

    # Session WITHOUT user_name (using {key?} won't error)
    await session_service.create_session(
        app_name="template_demo",
        user_id="user2",
        session_id="demo2b",
        state={}  # No user_name!
    )

    print("\n  Test B - Without name: state is empty")
    user_message = types.Content(parts=[types.Part(text="Hello!")])
    async for event in runner2.run_async(
        user_id="user2", session_id="demo2b", new_message=user_message
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text}")

    # =========================================================================
    # Demo 3: output_key
    # =========================================================================
    print("\n" + "="*60)
    print("DEMO 3: output_key - Save Response to State")
    print("="*60)

    runner3 = Runner(
        agent=poem_agent,
        app_name="template_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="template_demo",
        user_id="user3",
        session_id="demo3",
        state={"subject": "programming"}
    )

    print("\n  Step 1: Generate haiku with output_key='generated_poem'")
    user_message = types.Content(parts=[types.Part(text="Write a haiku")])
    async for event in runner3.run_async(
        user_id="user3", session_id="demo3", new_message=user_message
    ):
        if event.is_final_response() and event.content:
            print(f"  Haiku:\n  {event.content.parts[0].text}")

    # Check state - the poem should be saved
    session = await session_service.get_session(
        app_name="template_demo", user_id="user3", session_id="demo3"
    )
    saved_poem = session.state.get('generated_poem', 'NOT FOUND')
    print(f"\n  State now contains generated_poem: '{saved_poem[:50]}...'")

    # Now use the critic agent that reads from that state
    print("\n  Step 2: Critic reads {generated_poem} from state")
    runner4 = Runner(
        agent=poetry_critic,
        app_name="template_demo",
        session_service=session_service,
    )

    user_message = types.Content(parts=[types.Part(text="Review the poem")])
    async for event in runner4.run_async(
        user_id="user3", session_id="demo3", new_message=user_message
    ):
        if event.is_final_response() and event.content:
            print(f"  Critique: {event.content.parts[0].text}")

    # =========================================================================
    # Demo 4: InstructionProvider
    # =========================================================================
    print("\n" + "="*60)
    print("DEMO 4: InstructionProvider for Dynamic Instructions")
    print("="*60)

    runner5 = Runner(
        agent=dynamic_agent,
        app_name="template_demo",
        session_service=session_service,
    )

    # Beginner user
    await session_service.create_session(
        app_name="template_demo",
        user_id="user4",
        session_id="demo4a",
        state={
            "user_level": "beginner",
            "user_interests": ["Python", "web development"],
            "conversation_count": 0
        }
    )

    print("\n  Test A - Beginner user interested in Python, web dev")
    user_message = types.Content(parts=[types.Part(text="What is a variable?")])
    async for event in runner5.run_async(
        user_id="user4", session_id="demo4a", new_message=user_message
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text}")

    # Advanced user
    await session_service.create_session(
        app_name="template_demo",
        user_id="user4",
        session_id="demo4b",
        state={
            "user_level": "advanced",
            "user_interests": ["machine learning", "distributed systems"],
            "conversation_count": 5
        }
    )

    print("\n  Test B - Advanced user, ML/distributed systems, conversation #6")
    user_message = types.Content(parts=[types.Part(text="What is a variable?")])
    async for event in runner5.run_async(
        user_id="user4", session_id="demo4b", new_message=user_message
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text}")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: State in Instructions")
    print("#"*70)
    print("""
    METHOD 1: {key} Templating
    --------------------------
    instruction="Hello {user_name}, let's talk about {topic}."
    - Simple string replacement from state
    - ERROR if key doesn't exist

    METHOD 2: {key?} Optional Templating
    ------------------------------------
    instruction="Hello {user_name?}, welcome!"
    - Empty string if key doesn't exist
    - No error for missing keys

    METHOD 3: output_key
    --------------------
    agent = LlmAgent(..., output_key="response_key")
    - Automatically saves agent's response to state
    - Great for chaining agents (Agent A output -> Agent B input)

    METHOD 4: InstructionProvider Function
    --------------------------------------
    def my_provider(context: ReadonlyContext) -> str:
        return f"Dynamic instruction based on {context.state}"

    agent = LlmAgent(..., instruction=my_provider)
    - Full control over instruction generation
    - Can use complex logic
    - Can include literal {{braces}}
    - ReadonlyContext: can read state but NOT write

    WHEN TO USE EACH:
    -----------------
    - {key}: Simple personalization
    - {key?}: Optional personalization
    - output_key: Chaining agent outputs
    - InstructionProvider: Complex conditional instructions
    """)


if __name__ == "__main__":
    asyncio.run(main())
