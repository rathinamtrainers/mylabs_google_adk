"""
Lab 5 - Exercise 4: Custom Evaluators
======================================

This exercise covers advanced evaluation with custom rubrics:
1. Rubric-based response evaluation
2. Rubric-based tool use evaluation
3. Hallucination detection
4. Safety evaluation
5. Creating custom evaluation criteria

Run: uv run python 04_custom_evaluators.py
"""

import asyncio
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# =============================================================================
# Part 1: Introduction to Rubric-Based Evaluation
# =============================================================================

def explain_rubric_evaluation():
    """Explain rubric-based evaluation concepts."""
    print("""
    RUBRIC-BASED EVALUATION
    =======================

    Rubrics = Custom criteria you define to evaluate agent behavior

    WHY USE RUBRICS?
    ----------------
    - Evaluate qualities beyond simple matching
    - Define domain-specific success criteria
    - Assess tone, style, completeness
    - Validate complex workflows

    TWO TYPES OF RUBRIC EVALUATION:
    --------------------------------

    1. rubric_based_final_response_quality_v1
       - Evaluates the agent's RESPONSE
       - Questions like: "Is it concise?", "Is it helpful?"

    2. rubric_based_tool_use_quality_v1
       - Evaluates the agent's TOOL USAGE
       - Questions like: "Was the right tool called first?"

    HOW IT WORKS:
    -------------
    1. You define rubrics (yes/no questions)
    2. LLM-as-judge evaluates each rubric
    3. Each rubric scores 1.0 (yes) or 0.0 (no)
    4. Final score = average of all rubric scores

    EXAMPLE RUBRICS:
    ----------------
    Response rubrics:
    - "The response is concise (under 3 sentences)"
    - "The response includes the requested information"
    - "The response uses a professional tone"

    Tool use rubrics:
    - "The agent searches before providing details"
    - "The agent checks inventory before adding to cart"
    - "The agent uses the correct API for the task"
    """)


# =============================================================================
# Part 2: Response Quality Rubrics
# =============================================================================

def show_response_rubrics():
    """Show examples of response quality rubrics."""
    print("""
    RESPONSE QUALITY RUBRICS
    ========================

    CONFIGURATION:
    --------------
    {
      "criteria": {
        "rubric_based_final_response_quality_v1": {
          "threshold": 0.8,
          "judge_model_options": {
            "judge_model": "gemini-2.5-flash",
            "num_samples": 5
          },
          "rubrics": [
            {
              "rubric_id": "conciseness",
              "rubric_content": {
                "text_property": "The response is concise and to the point."
              }
            },
            {
              "rubric_id": "completeness",
              "rubric_content": {
                "text_property": "The response includes all requested information."
              }
            },
            {
              "rubric_id": "accuracy",
              "rubric_content": {
                "text_property": "The response contains accurate information from tools."
              }
            }
          ]
        }
      }
    }

    RUBRIC EXAMPLES BY DOMAIN:
    --------------------------

    Customer Service Agent:
    - "The response acknowledges the customer's issue"
    - "The response offers a clear solution or next step"
    - "The response maintains a helpful and empathetic tone"
    - "The response does not make promises it cannot keep"

    Technical Support Agent:
    - "The response includes specific troubleshooting steps"
    - "The response is technically accurate"
    - "The response avoids unnecessary jargon"
    - "The response asks clarifying questions when needed"

    Sales Agent:
    - "The response highlights product benefits"
    - "The response addresses the customer's stated needs"
    - "The response is not overly pushy or aggressive"
    - "The response includes relevant pricing information"

    Research Agent:
    - "The response cites sources for claims"
    - "The response acknowledges uncertainty where appropriate"
    - "The response provides balanced viewpoints"
    - "The response is well-organized"
    """)


# =============================================================================
# Part 3: Tool Use Quality Rubrics
# =============================================================================

def show_tool_use_rubrics():
    """Show examples of tool use quality rubrics."""
    print("""
    TOOL USE QUALITY RUBRICS
    ========================

    CONFIGURATION:
    --------------
    {
      "criteria": {
        "rubric_based_tool_use_quality_v1": {
          "threshold": 1.0,
          "judge_model_options": {
            "judge_model": "gemini-2.5-flash",
            "num_samples": 5
          },
          "rubrics": [
            {
              "rubric_id": "search_first",
              "rubric_content": {
                "text_property": "The agent calls search_products before get_product_details."
              }
            },
            {
              "rubric_id": "inventory_check",
              "rubric_content": {
                "text_property": "The agent checks inventory before adding items to cart."
              }
            },
            {
              "rubric_id": "correct_params",
              "rubric_content": {
                "text_property": "The agent uses the correct product_id from search results."
              }
            }
          ]
        }
      }
    }

    USE CASES:
    ----------

    E-commerce Workflow:
    - "Agent searches before getting details"
    - "Agent checks inventory before checkout"
    - "Agent validates user input before API calls"

    Data Pipeline:
    - "Agent retrieves data before transforming it"
    - "Agent validates data before saving"
    - "Agent logs actions for audit trail"

    Multi-Step Research:
    - "Agent searches multiple sources"
    - "Agent verifies information from different tools"
    - "Agent synthesizes results before responding"

    API Integration:
    - "Agent authenticates before API calls"
    - "Agent handles rate limiting appropriately"
    - "Agent retries failed requests"
    """)


# =============================================================================
# Part 4: Hallucination Detection
# =============================================================================

def explain_hallucination_detection():
    """Explain hallucination detection evaluation."""
    print("""
    HALLUCINATION DETECTION (hallucinations_v1)
    ===========================================

    Detects when an agent makes claims NOT supported by:
    - Tool outputs
    - System instructions
    - User-provided context

    HOW IT WORKS:
    -------------
    1. Agent response is split into sentences
    2. Each sentence is evaluated against context
    3. Sentences are labeled:
       - SUPPORTED: Backed by evidence
       - UNSUPPORTED: No evidence found
       - CONTRADICTORY: Contradicts evidence
       - DISPUTED: Conflicting evidence
       - NOT_APPLICABLE: Not a factual claim

    4. Score = (SUPPORTED + NOT_APPLICABLE) / Total

    CONFIGURATION:
    --------------
    {
      "criteria": {
        "hallucinations_v1": {
          "threshold": 0.8,
          "judge_model_options": {
            "judge_model": "gemini-2.5-flash"
          },
          "evaluate_intermediate_nl_responses": true
        }
      }
    }

    EXAMPLE:
    --------
    Tool output: {"product": "Laptop X", "price": 999, "stock": 5}

    Agent response: "The Laptop X costs $999 and we have 5 in stock."
    Evaluation:
      - "The Laptop X costs $999" -> SUPPORTED
      - "we have 5 in stock" -> SUPPORTED
    Score: 1.0 (no hallucinations)

    Agent response: "The Laptop X costs $899 and includes free shipping."
    Evaluation:
      - "The Laptop X costs $899" -> CONTRADICTORY (price is $999)
      - "includes free shipping" -> UNSUPPORTED (no evidence)
    Score: 0.0 (hallucinations detected!)

    WHEN TO USE:
    ------------
    - Factual accuracy is critical
    - Agent has access to specific data
    - Financial or medical information
    - Legal or compliance contexts
    """)


# =============================================================================
# Part 5: Safety Evaluation
# =============================================================================

def explain_safety_evaluation():
    """Explain safety evaluation."""
    print("""
    SAFETY EVALUATION (safety_v1)
    ============================

    Evaluates if agent responses are safe and appropriate.

    WHAT IT CHECKS:
    ---------------
    - Hate speech or discrimination
    - Harassment or threats
    - Dangerous information
    - Inappropriate content
    - Privacy violations
    - Illegal activities

    CONFIGURATION:
    --------------
    {
      "criteria": {
        "safety_v1": 0.8
      }
    }

    NOTE: Requires Google Cloud Project
    Set environment variables:
    - GOOGLE_CLOUD_PROJECT
    - GOOGLE_CLOUD_LOCATION

    WHEN TO USE:
    ------------
    - User-facing applications
    - Public deployments
    - Sensitive domains
    - Compliance requirements

    COMBINING WITH OTHER METRICS:
    -----------------------------
    {
      "criteria": {
        "safety_v1": 0.95,           // High threshold for safety
        "hallucinations_v1": 0.8,    // Factual accuracy
        "rubric_based_final_response_quality_v1": {
          "threshold": 0.7,
          "rubrics": [...]
        }
      }
    }
    """)


# =============================================================================
# Part 6: Sample Agent for Custom Evaluation
# =============================================================================

def get_account_balance(account_id: str) -> dict:
    """Get account balance."""
    balances = {
        "ACC001": {"balance": 5000.00, "currency": "USD", "type": "checking"},
        "ACC002": {"balance": 15000.00, "currency": "USD", "type": "savings"},
    }
    return balances.get(account_id, {"error": "Account not found"})


def transfer_funds(from_account: str, to_account: str, amount: float) -> dict:
    """Transfer funds between accounts."""
    if amount <= 0:
        return {"error": "Amount must be positive"}
    return {"success": True, "message": f"Transferred ${amount} from {from_account} to {to_account}"}


def get_transaction_history(account_id: str, limit: int = 5) -> dict:
    """Get recent transactions."""
    transactions = {
        "ACC001": [
            {"date": "2024-01-15", "description": "Direct Deposit", "amount": 2500.00},
            {"date": "2024-01-12", "description": "Grocery Store", "amount": -85.50},
        ],
    }
    return {"transactions": transactions.get(account_id, [])}


def create_banking_agent():
    """Create a banking assistant agent."""
    balance_tool = FunctionTool(func=get_account_balance)
    transfer_tool = FunctionTool(func=transfer_funds)
    history_tool = FunctionTool(func=get_transaction_history)

    agent = LlmAgent(
        name="BankingAgent",
        model="gemini-2.0-flash",
        instruction="""You are a banking assistant.
        Help customers with account inquiries and transactions.

        IMPORTANT RULES:
        1. Always verify account exists before transfers
        2. Never disclose full account numbers
        3. Confirm transaction details before executing
        4. Be professional and security-conscious
        5. Do not provide financial advice""",
        tools=[balance_tool, transfer_tool, history_tool],
    )

    return agent


async def run_banking_agent_demo():
    """Run the banking agent to demonstrate evaluation scenarios."""
    print("\n  Running banking agent for evaluation demo...")

    agent = create_banking_agent()
    session_service = InMemorySessionService()

    runner = Runner(
        agent=agent,
        app_name="banking_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="banking_demo",
        user_id="user1",
        session_id="banking_session",
        state={}
    )

    queries = [
        "What's my balance for account ACC001?",
        "Transfer $500 from ACC001 to ACC002",
    ]

    for query in queries:
        print(f"\n  Query: '{query}'")

        user_message = types.Content(parts=[types.Part(text=query)])

        async for event in runner.run_async(
            user_id="user1",
            session_id="banking_session",
            new_message=user_message,
        ):
            if event.is_final_response() and event.content:
                response = event.content.parts[0].text
                print(f"  Response: {response[:150]}...")


# =============================================================================
# Part 7: Complete Rubric Configuration Example
# =============================================================================

def show_complete_config():
    """Show a complete evaluation configuration with all rubric types."""
    print("""
    COMPLETE EVALUATION CONFIGURATION
    ==================================

    {
      "criteria": {
        // 1. Basic trajectory matching
        "tool_trajectory_avg_score": {
          "threshold": 0.9,
          "match_type": "IN_ORDER"
        },

        // 2. Basic response matching
        "response_match_score": 0.7,

        // 3. Semantic response matching
        "final_response_match_v2": {
          "threshold": 0.8,
          "judge_model_options": {
            "judge_model": "gemini-2.5-flash",
            "num_samples": 3
          }
        },

        // 4. Custom response rubrics
        "rubric_based_final_response_quality_v1": {
          "threshold": 0.8,
          "judge_model_options": {
            "judge_model": "gemini-2.5-flash",
            "num_samples": 3
          },
          "rubrics": [
            {
              "rubric_id": "professionalism",
              "rubric_content": {
                "text_property": "The response maintains a professional banking tone."
              }
            },
            {
              "rubric_id": "security",
              "rubric_content": {
                "text_property": "The response does not reveal sensitive information."
              }
            },
            {
              "rubric_id": "accuracy",
              "rubric_content": {
                "text_property": "The response accurately reflects tool output data."
              }
            },
            {
              "rubric_id": "completeness",
              "rubric_content": {
                "text_property": "The response answers the user's question completely."
              }
            }
          ]
        },

        // 5. Custom tool use rubrics
        "rubric_based_tool_use_quality_v1": {
          "threshold": 1.0,
          "judge_model_options": {
            "judge_model": "gemini-2.5-flash",
            "num_samples": 3
          },
          "rubrics": [
            {
              "rubric_id": "balance_check",
              "rubric_content": {
                "text_property": "Agent checks balance before transfers."
              }
            },
            {
              "rubric_id": "account_validation",
              "rubric_content": {
                "text_property": "Agent validates account exists before operations."
              }
            }
          ]
        },

        // 6. Hallucination detection
        "hallucinations_v1": {
          "threshold": 0.9,
          "evaluate_intermediate_nl_responses": true
        },

        // 7. Safety check
        "safety_v1": 0.95
      }
    }
    """)


# =============================================================================
# Part 8: Best Practices for Custom Rubrics
# =============================================================================

def show_rubric_best_practices():
    """Show best practices for writing custom rubrics."""
    print("""
    RUBRIC WRITING BEST PRACTICES
    =============================

    1. BE SPECIFIC:
       -------------
       BAD:  "The response is good"
       GOOD: "The response includes the account balance in dollars"

    2. MAKE IT EVALUABLE:
       ------------------
       BAD:  "The response feels professional"
       GOOD: "The response uses formal language and avoids slang"

    3. ONE CONCEPT PER RUBRIC:
       -----------------------
       BAD:  "The response is accurate and concise"
       GOOD: Separate into two rubrics:
             - "The response contains accurate information"
             - "The response is under 3 sentences"

    4. AVOID AMBIGUITY:
       -----------------
       BAD:  "The response is short"
       GOOD: "The response is 50 words or fewer"

    5. TEST YOUR RUBRICS:
       ------------------
       - Run with known good/bad responses
       - Check if rubric scores match expectations
       - Adjust wording if needed

    6. USE DOMAIN LANGUAGE:
       --------------------
       Banking: "complies with KYC requirements"
       Medical: "includes appropriate disclaimers"
       Legal: "cites relevant precedents"

    7. PRIORITIZE RUBRICS:
       -------------------
       - Safety rubrics: threshold 0.95+
       - Accuracy rubrics: threshold 0.85+
       - Style rubrics: threshold 0.7+

    RUBRIC TEMPLATE:
    ----------------
    {
      "rubric_id": "unique_identifier",      // snake_case
      "rubric_content": {
        "text_property": "Clear yes/no statement about the response."
      }
    }
    """)


async def main():
    print("\n" + "#"*70)
    print("# Lab 5 Exercise 4: Custom Evaluators")
    print("#"*70)

    # =========================================================================
    # Part 1: Introduction
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: Introduction to Rubric-Based Evaluation")
    print("="*60)
    explain_rubric_evaluation()

    # =========================================================================
    # Part 2: Response Rubrics
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: Response Quality Rubrics")
    print("="*60)
    show_response_rubrics()

    # =========================================================================
    # Part 3: Tool Use Rubrics
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: Tool Use Quality Rubrics")
    print("="*60)
    show_tool_use_rubrics()

    # =========================================================================
    # Part 4: Hallucination Detection
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Hallucination Detection")
    print("="*60)
    explain_hallucination_detection()

    # =========================================================================
    # Part 5: Safety Evaluation
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: Safety Evaluation")
    print("="*60)
    explain_safety_evaluation()

    # =========================================================================
    # Part 6: Demo Agent
    # =========================================================================
    print("\n" + "="*60)
    print("PART 6: Banking Agent Demo")
    print("="*60)

    await run_banking_agent_demo()

    # =========================================================================
    # Part 7: Complete Config
    # =========================================================================
    print("\n" + "="*60)
    print("PART 7: Complete Configuration Example")
    print("="*60)
    show_complete_config()

    # =========================================================================
    # Part 8: Best Practices
    # =========================================================================
    print("\n" + "="*60)
    print("PART 8: Rubric Writing Best Practices")
    print("="*60)
    show_rubric_best_practices()

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Custom Evaluators")
    print("#"*70)
    print("""
    CUSTOM EVALUATION METRICS:
    --------------------------

    1. rubric_based_final_response_quality_v1
       - Evaluates response quality with custom rubrics
       - Good for: tone, style, completeness, domain-specific criteria

    2. rubric_based_tool_use_quality_v1
       - Evaluates tool usage patterns with custom rubrics
       - Good for: workflow validation, order of operations

    3. hallucinations_v1
       - Detects unsupported or contradictory claims
       - Good for: factual accuracy, data integrity

    4. safety_v1
       - Checks for harmful content
       - Good for: user-facing applications, compliance

    RUBRIC STRUCTURE:
    -----------------
    {
      "rubric_id": "unique_id",
      "rubric_content": {
        "text_property": "Clear yes/no statement"
      }
    }

    KEY TAKEAWAYS:
    --------------
    - Rubrics let you define custom success criteria
    - LLM-as-judge evaluates rubrics
    - Be specific and evaluable in rubric wording
    - Combine multiple metrics for comprehensive evaluation
    - Use high thresholds for safety-critical rubrics
    """)


if __name__ == "__main__":
    asyncio.run(main())
