"""
Lab 8 - Exercise 4: Agent Cards
===============================

This exercise covers agent card generation and customization:
1. AgentCardBuilder automatic generation
2. Agent card structure and fields
3. Custom skills and tags
4. Input/output modes configuration
5. Saving and loading agent cards

Run: uv run python 04_agent_cards.py
"""

import asyncio
import json
from pathlib import Path
from google.adk.agents import LlmAgent
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder


# =============================================================================
# Part 1: Agent Card Structure
# =============================================================================

def explain_agent_card_structure():
    """Explain the structure of an A2A agent card."""
    print("""
    AGENT CARD STRUCTURE
    ====================

    An agent card is a JSON document that describes an A2A agent.
    Think of it as a "business card" or "API spec" for AI agents.


    REQUIRED FIELDS:
    ----------------
    {
      "name": "AgentName",           // Unique identifier
      "url": "http://host:port/",    // Where to reach the agent
      "version": "1.0.0",            // API version
    }


    OPTIONAL FIELDS:
    ----------------
    {
      "description": "What the agent does",
      "skills": [...],               // List of capabilities
      "capabilities": {...},         // Feature flags
      "defaultInputModes": [...],    // Supported input types
      "defaultOutputModes": [...],   // Supported output types
      "supportsAuthenticatedExtendedCard": false
    }


    SKILLS STRUCTURE:
    -----------------
    "skills": [
      {
        "id": "unique_skill_id",
        "name": "Human Readable Name",
        "description": "What this skill does",
        "tags": ["tag1", "tag2"]
      }
    ]

    Skills tell clients what the agent can do.
    This helps with discovery and routing.


    INPUT/OUTPUT MODES:
    -------------------
    "defaultInputModes": ["text/plain", "application/json"],
    "defaultOutputModes": ["text/plain"]

    Specifies MIME types the agent accepts/produces.
    """)


# =============================================================================
# Part 2: AgentCardBuilder
# =============================================================================

def explain_agent_card_builder():
    """Explain the AgentCardBuilder class."""
    print("""
    AGENTCARDBUILDER
    ================

    AgentCardBuilder automatically generates agent cards from ADK agents.


    BASIC USAGE:
    ------------
    from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder

    agent = LlmAgent(name="MyAgent", ...)

    builder = AgentCardBuilder(
        agent=agent,
        rpc_url="http://localhost:8001"
    )

    agent_card = builder.build()


    WHAT IT EXTRACTS:
    -----------------
    1. name: From agent.name
    2. description: From agent.description
    3. url: From rpc_url parameter
    4. skills: From agent's tools and sub-agents
    5. version: Defaults to "0.0.1"


    SKILL DETECTION:
    ----------------
    The builder creates skills from:
    - The main agent capability
    - Each tool's docstring and name
    - Each sub-agent's description


    LIMITATIONS:
    ------------
    - Cannot detect all capabilities automatically
    - Skills may need manual refinement
    - Custom capabilities need manual config
    """)


# =============================================================================
# Part 3: Demo - Building Agent Cards
# =============================================================================

def create_demo_agent():
    """Create a demo agent with tools."""

    def search_products(query: str, max_results: int = 5) -> list:
        """Search for products matching a query.

        Args:
            query: Search terms
            max_results: Maximum number of results (1-20)

        Returns:
            List of matching products
        """
        return [
            {"name": f"Product {i}", "price": 10.0 * i}
            for i in range(1, min(max_results, 5) + 1)
        ]

    def get_product_details(product_id: str) -> dict:
        """Get detailed information about a product.

        Args:
            product_id: The product identifier

        Returns:
            Product details including name, price, description
        """
        return {
            "id": product_id,
            "name": f"Product {product_id}",
            "price": 29.99,
            "description": "A great product",
            "in_stock": True,
        }

    def add_to_cart(product_id: str, quantity: int = 1) -> dict:
        """Add a product to the shopping cart.

        Args:
            product_id: The product to add
            quantity: Number of items to add

        Returns:
            Updated cart status
        """
        return {
            "success": True,
            "product_id": product_id,
            "quantity": quantity,
            "message": f"Added {quantity} item(s) to cart",
        }

    return LlmAgent(
        name="ShoppingAssistant",
        model="gemini-2.0-flash",
        description="An e-commerce shopping assistant that helps customers "
                    "find products, view details, and manage their cart.",
        instruction="""You are a shopping assistant.
        Help customers:
        - Search for products
        - View product details
        - Add items to cart
        Be helpful and suggest relevant products.""",
        tools=[search_products, get_product_details, add_to_cart],
    )


async def demo_build_agent_card():
    """Demonstrate building an agent card."""
    print("\n  Creating demo agent...")
    agent = create_demo_agent()

    print(f"  Agent: {agent.name}")
    print(f"  Description: {agent.description}")
    print(f"  Tools: {len(agent.tools)}")

    # Build agent card
    print("\n  Building agent card with AgentCardBuilder...")

    builder = AgentCardBuilder(
        agent=agent,
        rpc_url="http://localhost:8001",
    )

    agent_card = await builder.build()

    # Display the card
    print("\n  Generated Agent Card:")
    print("-" * 40)

    # Convert to dict for display
    card_dict = {
        "name": agent_card.name,
        "description": agent_card.description,
        "url": agent_card.url,
        "version": agent_card.version,
        "skills": [
            {
                "id": skill.id,
                "name": skill.name,
                "description": skill.description,
                "tags": skill.tags,
            }
            for skill in (agent_card.skills or [])
        ],
        "defaultInputModes": agent_card.default_input_modes,
        "defaultOutputModes": agent_card.default_output_modes,
    }

    print(json.dumps(card_dict, indent=2))

    return agent_card


# =============================================================================
# Part 4: Custom Skills and Tags
# =============================================================================

def explain_custom_skills():
    """Explain how to customize skills and tags."""
    print("""
    CUSTOM SKILLS AND TAGS
    ======================

    While AgentCardBuilder auto-generates skills, you can customize them.


    WHY CUSTOMIZE SKILLS?
    ---------------------
    1. Better descriptions for discovery
    2. Specific tags for categorization
    3. Group related capabilities
    4. Hide internal tools


    MANUAL SKILL CREATION:
    ----------------------
    from a2a.types import AgentSkill

    skill = AgentSkill(
        id="product_search",
        name="Product Search",
        description="Search our catalog of 10,000+ products",
        tags=["search", "catalog", "products"]
    )


    SKILL TAGS:
    -----------
    Tags help categorize and discover agents:
    - Domain: ["ecommerce", "finance", "healthcare"]
    - Capability: ["search", "write", "analyze"]
    - Language: ["english", "spanish", "multilingual"]


    CUSTOM AGENT CARD WITH to_a2a():
    ---------------------------------
    You can pass a complete agent card to to_a2a():

    custom_card = AgentCard(
        name="CustomAgent",
        url="http://...",
        skills=[custom_skill_1, custom_skill_2],
        ...
    )

    app = to_a2a(agent=agent, agent_card=custom_card)


    OR FROM FILE:
    -------------
    app = to_a2a(agent=agent, agent_card="/path/to/card.json")
    """)


# =============================================================================
# Part 5: Input/Output Modes
# =============================================================================

def explain_io_modes():
    """Explain input/output modes configuration."""
    print("""
    INPUT/OUTPUT MODES
    ==================

    Modes specify what MIME types the agent handles.


    DEFAULT MODES:
    --------------
    By default, AgentCardBuilder sets:
    - defaultInputModes: ["text/plain"]
    - defaultOutputModes: ["text/plain"]


    COMMON MIME TYPES:
    ------------------
    Text:
    - text/plain: Plain text
    - text/markdown: Markdown formatted text
    - text/html: HTML content

    Data:
    - application/json: JSON data
    - application/xml: XML data

    Media:
    - image/png: PNG images
    - image/jpeg: JPEG images
    - audio/mpeg: MP3 audio
    - video/mp4: MP4 video

    Documents:
    - application/pdf: PDF files


    MULTIMODAL AGENTS:
    ------------------
    For agents that handle multiple types:

    {
      "defaultInputModes": [
        "text/plain",
        "image/png",
        "image/jpeg"
      ],
      "defaultOutputModes": [
        "text/plain",
        "image/png"
      ]
    }

    This tells clients the agent can:
    - Accept text and images as input
    - Produce text and images as output
    """)


# =============================================================================
# Part 6: Saving and Loading Agent Cards
# =============================================================================

async def demo_save_load_card():
    """Demonstrate saving and loading agent cards."""
    print("\n  Demonstrating agent card file operations...")

    # Create agent and build card
    agent = create_demo_agent()
    builder = AgentCardBuilder(
        agent=agent,
        rpc_url="http://localhost:8001",
    )
    agent_card = await builder.build()

    # Save to file
    card_path = Path("/tmp/shopping_assistant_card.json")

    card_dict = {
        "name": agent_card.name,
        "description": agent_card.description,
        "url": agent_card.url,
        "version": agent_card.version,
        "skills": [
            {
                "id": skill.id,
                "name": skill.name,
                "description": skill.description,
                "tags": skill.tags,
            }
            for skill in (agent_card.skills or [])
        ],
        "defaultInputModes": agent_card.default_input_modes,
        "defaultOutputModes": agent_card.default_output_modes,
        "capabilities": {},
    }

    print(f"\n  Saving agent card to: {card_path}")
    with open(card_path, "w") as f:
        json.dump(card_dict, f, indent=2)
    print("  Card saved successfully!")

    # Load from file
    print(f"\n  Loading agent card from: {card_path}")
    with open(card_path, "r") as f:
        loaded_card = json.load(f)

    print("  Card loaded successfully!")
    print(f"    Name: {loaded_card['name']}")
    print(f"    URL: {loaded_card['url']}")
    print(f"    Skills: {len(loaded_card.get('skills', []))}")

    print("""

    USING FILE-BASED CARDS:
    -----------------------
    # When exposing:
    app = to_a2a(
        agent=agent,
        agent_card="/path/to/custom-card.json"
    )

    # When consuming:
    remote = RemoteA2aAgent(
        name="remote",
        agent_card="/path/to/card.json"  # Works with local files too
    )
    """)


# =============================================================================
# Main
# =============================================================================

async def main():
    print("\n" + "#" * 70)
    print("# Lab 8 Exercise 4: Agent Cards")
    print("#" * 70)

    # =========================================================================
    # Part 1: Agent Card Structure
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 1: Agent Card Structure")
    print("=" * 60)

    explain_agent_card_structure()

    # =========================================================================
    # Part 2: AgentCardBuilder
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 2: AgentCardBuilder")
    print("=" * 60)

    explain_agent_card_builder()

    # =========================================================================
    # Part 3: Building Agent Cards
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 3: Building Agent Cards (Demo)")
    print("=" * 60)

    await demo_build_agent_card()

    # =========================================================================
    # Part 4: Custom Skills and Tags
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 4: Custom Skills and Tags")
    print("=" * 60)

    explain_custom_skills()

    # =========================================================================
    # Part 5: Input/Output Modes
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 5: Input/Output Modes")
    print("=" * 60)

    explain_io_modes()

    # =========================================================================
    # Part 6: Saving and Loading
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 6: Saving and Loading Agent Cards")
    print("=" * 60)

    await demo_save_load_card()

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#" * 70)
    print("# Summary: Agent Cards")
    print("#" * 70)
    print("""
    AGENT CARD PURPOSE:
    -------------------
    - Describe agent capabilities
    - Enable discovery and routing
    - Specify supported formats
    - Document the agent API

    KEY FIELDS:
    -----------
    - name: Agent identifier
    - url: Service endpoint
    - description: What it does
    - skills: List of capabilities
    - version: API version
    - defaultInputModes/defaultOutputModes: MIME types

    AGENTCARDBUILDER:
    -----------------
    builder = AgentCardBuilder(
        agent=agent,
        rpc_url="http://localhost:8001"
    )
    card = builder.build()

    AUTO-GENERATED SKILLS:
    ----------------------
    - Main agent capability
    - Tools from agent.tools
    - Sub-agent capabilities

    CUSTOMIZATION OPTIONS:
    ----------------------
    1. Pass custom AgentCard to to_a2a()
    2. Load from JSON file
    3. Manually construct AgentCard

    FILE-BASED CARDS:
    -----------------
    # Save
    json.dump(card_dict, open("card.json", "w"))

    # Load in to_a2a or RemoteA2aAgent
    app = to_a2a(agent=agent, agent_card="card.json")

    BEST PRACTICES:
    ---------------
    1. Write clear, descriptive skill names
    2. Use meaningful tags for discovery
    3. Specify all supported MIME types
    4. Version your agent cards
    5. Keep descriptions concise but complete

    NEXT STEPS:
    -----------
    Exercise 5: Build a distributed multi-agent system
    """)


if __name__ == "__main__":
    asyncio.run(main())
