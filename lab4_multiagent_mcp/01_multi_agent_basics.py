"""
Lab 4 - Exercise 1: Multi-Agent Basics
=======================================

This exercise demonstrates the fundamentals of multi-agent systems:
1. Creating agents with sub-agents
2. Agent hierarchy (parent-child)
3. Agent transfer (delegation)
4. Agent descriptions for routing

Run: uv run python 01_multi_agent_basics.py
"""

import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# =============================================================================
# Part 1: Simple Sub-Agent Structure
# =============================================================================

def create_customer_service_team():
    """
    Create a team of specialized agents with a coordinator.

    Hierarchy:
        Coordinator
        ├── BillingAgent (handles billing questions)
        ├── TechSupportAgent (handles technical issues)
        └── GeneralAgent (handles everything else)
    """

    # Specialized agents (children)
    billing_agent = LlmAgent(
        name="BillingAgent",
        model="gemini-2.0-flash",
        description="Handles billing inquiries, payments, invoices, and account charges.",
        instruction="""You are a billing specialist.
        Help customers with:
        - Invoice questions
        - Payment issues
        - Account charges
        - Subscription changes
        Keep responses concise and professional.""",
    )

    tech_support_agent = LlmAgent(
        name="TechSupportAgent",
        model="gemini-2.0-flash",
        description="Handles technical issues, troubleshooting, and product problems.",
        instruction="""You are a technical support specialist.
        Help customers with:
        - Product troubleshooting
        - Technical errors
        - How-to questions
        - Bug reports
        Keep responses clear and helpful.""",
    )

    general_agent = LlmAgent(
        name="GeneralAgent",
        model="gemini-2.0-flash",
        description="Handles general inquiries, greetings, and questions not related to billing or tech.",
        instruction="""You are a general customer service representative.
        Help with:
        - General questions
        - Company information
        - Greetings and farewells
        Keep responses friendly and brief.""",
    )

    # Coordinator agent (parent)
    coordinator = LlmAgent(
        name="CustomerServiceCoordinator",
        model="gemini-2.0-flash",
        description="Main coordinator that routes customer requests to specialists.",
        instruction="""You are a customer service coordinator.

        Your job is to:
        1. Understand the customer's request
        2. Route to the appropriate specialist:
           - BillingAgent: for billing, payment, invoice questions
           - TechSupportAgent: for technical issues and troubleshooting
           - GeneralAgent: for general inquiries

        If a request is clearly about billing or tech, transfer immediately.
        For ambiguous requests, ask for clarification first.

        Use transfer_to_agent to delegate to specialists.""",
        sub_agents=[billing_agent, tech_support_agent, general_agent],
    )

    return coordinator


# =============================================================================
# Part 2: Understanding Agent Hierarchy
# =============================================================================

def demonstrate_hierarchy():
    """Show how agent hierarchy works."""

    child1 = LlmAgent(name="Child1", model="gemini-2.0-flash")
    child2 = LlmAgent(name="Child2", model="gemini-2.0-flash")

    parent = LlmAgent(
        name="Parent",
        model="gemini-2.0-flash",
        sub_agents=[child1, child2]
    )

    print("\n  Agent Hierarchy Demo:")
    print(f"    Parent: {parent.name}")
    print(f"    Sub-agents: {[a.name for a in parent.sub_agents]}")

    # Note: parent_agent is set by the framework during execution
    print(f"    Child1.parent_agent: {getattr(child1, 'parent_agent', 'Not set yet')}")


async def main():
    print("\n" + "#"*70)
    print("# Lab 4 Exercise 1: Multi-Agent Basics")
    print("#"*70)

    session_service = InMemorySessionService()

    # =========================================================================
    # Part 1: Agent Hierarchy
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: Understanding Agent Hierarchy")
    print("="*60)

    demonstrate_hierarchy()

    print("""
    KEY CONCEPTS:
    - Parent agent has sub_agents list
    - sub_agents are specialized workers
    - Parent can transfer control to children
    - Children don't know about each other directly
    """)

    # =========================================================================
    # Part 2: Agent Transfer in Action
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: Agent Transfer in Action")
    print("="*60)

    coordinator = create_customer_service_team()

    runner = Runner(
        agent=coordinator,
        app_name="customer_service",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="customer_service",
        user_id="customer1",
        session_id="support_session",
        state={}
    )

    # Test different types of requests
    test_messages = [
        ("Billing request", "I need help with my invoice. I was charged twice."),
        ("Tech request", "My app keeps crashing when I try to login."),
        ("General request", "What are your business hours?"),
    ]

    for label, message in test_messages:
        print(f"\n  --- {label} ---")
        print(f"  Customer: {message}")

        user_message = types.Content(parts=[types.Part(text=message)])

        response_text = ""
        responding_agent = ""

        async for event in runner.run_async(
            user_id="customer1",
            session_id="support_session",
            new_message=user_message,
        ):
            # Track which agent responds
            if hasattr(event, 'author'):
                responding_agent = event.author

            if event.is_final_response() and event.content:
                response_text = event.content.parts[0].text

        print(f"  Responding Agent: {responding_agent}")
        print(f"  Response: {response_text[:120]}...")

    # =========================================================================
    # Part 3: How Transfer Works
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: How Agent Transfer Works")
    print("="*60)

    print("""
    TRANSFER MECHANISM:
    -------------------

    1. User sends message to Coordinator

    2. Coordinator's LLM analyzes the message

    3. LLM generates a special function call:
       transfer_to_agent(agent_name='BillingAgent')

    4. ADK Framework:
       - Finds BillingAgent in sub_agents
       - Transfers execution to BillingAgent
       - BillingAgent processes and responds

    5. Response goes back to user

    IMPORTANT: The transfer is automatic based on LLM decision.
    The LLM uses the 'description' field to choose which agent.
    """)

    # =========================================================================
    # Part 4: Agent Description Best Practices
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Agent Description Best Practices")
    print("="*60)

    print("""
    DESCRIPTION FIELD:
    ------------------
    The 'description' field is CRITICAL for multi-agent routing.

    The coordinator's LLM reads descriptions to decide where to route.

    GOOD DESCRIPTION:
    -----------------
    description="Handles billing inquiries including invoices,
                 payments, refunds, and subscription changes."

    BAD DESCRIPTION:
    ----------------
    description="Billing agent"  # Too vague!

    TIPS:
    -----
    1. Be specific about what the agent handles
    2. List key topics and keywords
    3. Mention what it DOESN'T handle if helpful
    4. Keep it concise but comprehensive
    """)

    # =========================================================================
    # Part 5: Manual Sub-Agent Invocation (Alternative)
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: Explicit vs Implicit Delegation")
    print("="*60)

    print("""
    TWO WAYS TO USE SUB-AGENTS:
    ---------------------------

    1. IMPLICIT (Agent Transfer) - What we just saw
       - Coordinator uses transfer_to_agent()
       - LLM decides when to transfer
       - Automatic, flexible
       - Good for: Customer service, routing

    2. EXPLICIT (AgentTool) - We'll cover in Exercise 3
       - Wrap agent in AgentTool
       - Parent explicitly calls agent as a tool
       - More control, deterministic
       - Good for: Specific tasks, pipelines

    WHEN TO USE WHICH:
    ------------------

    Agent Transfer (Implicit):
    - Routing based on user intent
    - Conversation hand-off
    - Customer service scenarios

    AgentTool (Explicit):
    - Agent does specific computation
    - Results needed by parent
    - Pipeline/workflow scenarios
    """)

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Multi-Agent Basics")
    print("#"*70)
    print("""
    MULTI-AGENT STRUCTURE:
    ----------------------
    coordinator = LlmAgent(
        name="Coordinator",
        description="Routes requests to specialists",
        instruction="Route to appropriate sub-agent...",
        sub_agents=[agent_a, agent_b, agent_c]
    )

    SUB-AGENT REQUIREMENTS:
    -----------------------
    1. name: Unique identifier
    2. description: CRITICAL for routing decisions
    3. instruction: How the agent should behave
    4. model: LLM model to use

    AGENT TRANSFER:
    ---------------
    - LLM automatically calls transfer_to_agent()
    - Based on sub-agent descriptions
    - Control transfers to child agent
    - Child responds directly to user

    HIERARCHY:
    ----------
    - Parent knows its children (sub_agents list)
    - Children get parent reference during execution
    - Children don't know about siblings

    USE CASES:
    ----------
    - Customer service routing
    - Specialized task delegation
    - Team of expert agents
    - Conversational hand-offs
    """)


if __name__ == "__main__":
    asyncio.run(main())
