# Exercise 4: Custom Evaluators

## Overview

This exercise covers advanced evaluation techniques using custom rubrics, hallucination detection, and safety evaluation.

**File**: `04_custom_evaluators.py`

## Learning Objectives

1. Create custom rubrics for response quality
2. Create custom rubrics for tool use quality
3. Implement hallucination detection
4. Configure safety evaluation
5. Combine multiple evaluation metrics

## Part 1: Introduction to Rubric-Based Evaluation

### What are Rubrics?

**Rubrics** = Custom yes/no criteria you define to evaluate agent behavior

### Why Use Rubrics?

1. **Beyond basic matching**: Evaluate qualities like tone, completeness, style
2. **Domain-specific criteria**: Define success based on your requirements
3. **Complex workflows**: Validate multi-step processes
4. **Quality assessment**: Measure aspects that matter to your use case

### Two Types of Rubric Evaluation

#### 1. Response Quality Rubrics
**Metric**: `rubric_based_final_response_quality_v1`

**Evaluates**: The agent's final response

**Example rubrics**:
- "Is the response concise?"
- "Does it include all requested information?"
- "Is the tone professional?"

#### 2. Tool Use Quality Rubrics
**Metric**: `rubric_based_tool_use_quality_v1`

**Evaluates**: The agent's tool usage

**Example rubrics**:
- "Was the search tool called before details?"
- "Did agent check inventory before adding to cart?"

### How Rubrics Work

1. **Define rubrics** as yes/no questions
2. **LLM-as-judge** evaluates each rubric
3. **Each rubric** scores 1.0 (yes) or 0.0 (no)
4. **Final score** = average of all rubric scores

**Example**:
```
Rubric 1: "Response is concise" → 1.0 (yes)
Rubric 2: "Response includes all info" → 1.0 (yes)
Rubric 3: "Response uses professional tone" → 0.0 (no)

Final score: (1.0 + 1.0 + 0.0) / 3 = 0.67
```

## Part 2: Response Quality Rubrics

### Configuration

```json
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
```

### Rubric Structure

```json
{
  "rubric_id": "unique_identifier",      // snake_case identifier
  "rubric_content": {
    "text_property": "Clear yes/no statement about the response."
  }
}
```

### Domain-Specific Examples

#### Customer Service Agent

```json
"rubrics": [
  {
    "rubric_id": "acknowledgment",
    "rubric_content": {
      "text_property": "The response acknowledges the customer's issue."
    }
  },
  {
    "rubric_id": "solution",
    "rubric_content": {
      "text_property": "The response offers a clear solution or next step."
    }
  },
  {
    "rubric_id": "empathy",
    "rubric_content": {
      "text_property": "The response maintains a helpful and empathetic tone."
    }
  },
  {
    "rubric_id": "realistic",
    "rubric_content": {
      "text_property": "The response does not make promises it cannot keep."
    }
  }
]
```

#### Technical Support Agent

```json
"rubrics": [
  {
    "rubric_id": "troubleshooting",
    "rubric_content": {
      "text_property": "The response includes specific troubleshooting steps."
    }
  },
  {
    "rubric_id": "accuracy",
    "rubric_content": {
      "text_property": "The response is technically accurate."
    }
  },
  {
    "rubric_id": "clarity",
    "rubric_content": {
      "text_property": "The response avoids unnecessary jargon."
    }
  },
  {
    "rubric_id": "clarification",
    "rubric_content": {
      "text_property": "The response asks clarifying questions when needed."
    }
  }
]
```

#### Sales Agent

```json
"rubrics": [
  {
    "rubric_id": "benefits",
    "rubric_content": {
      "text_property": "The response highlights product benefits."
    }
  },
  {
    "rubric_id": "personalization",
    "rubric_content": {
      "text_property": "The response addresses the customer's stated needs."
    }
  },
  {
    "rubric_id": "tone",
    "rubric_content": {
      "text_property": "The response is not overly pushy or aggressive."
    }
  },
  {
    "rubric_id": "pricing",
    "rubric_content": {
      "text_property": "The response includes relevant pricing information."
    }
  }
]
```

#### Research Agent

```json
"rubrics": [
  {
    "rubric_id": "citations",
    "rubric_content": {
      "text_property": "The response cites sources for claims."
    }
  },
  {
    "rubric_id": "uncertainty",
    "rubric_content": {
      "text_property": "The response acknowledges uncertainty where appropriate."
    }
  },
  {
    "rubric_id": "balance",
    "rubric_content": {
      "text_property": "The response provides balanced viewpoints."
    }
  },
  {
    "rubric_id": "organization",
    "rubric_content": {
      "text_property": "The response is well-organized."
    }
  }
]
```

## Part 3: Tool Use Quality Rubrics

### Configuration

```json
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
```

### Use Case Examples

#### E-commerce Workflow

```json
"rubrics": [
  {
    "rubric_id": "search_before_details",
    "rubric_content": {
      "text_property": "Agent searches before getting details."
    }
  },
  {
    "rubric_id": "inventory_before_checkout",
    "rubric_content": {
      "text_property": "Agent checks inventory before checkout."
    }
  },
  {
    "rubric_id": "input_validation",
    "rubric_content": {
      "text_property": "Agent validates user input before API calls."
    }
  }
]
```

#### Data Pipeline

```json
"rubrics": [
  {
    "rubric_id": "retrieve_before_transform",
    "rubric_content": {
      "text_property": "Agent retrieves data before transforming it."
    }
  },
  {
    "rubric_id": "validate_before_save",
    "rubric_content": {
      "text_property": "Agent validates data before saving."
    }
  },
  {
    "rubric_id": "audit_logging",
    "rubric_content": {
      "text_property": "Agent logs actions for audit trail."
    }
  }
]
```

#### Multi-Step Research

```json
"rubrics": [
  {
    "rubric_id": "multiple_sources",
    "rubric_content": {
      "text_property": "Agent searches multiple sources."
    }
  },
  {
    "rubric_id": "verification",
    "rubric_content": {
      "text_property": "Agent verifies information from different tools."
    }
  },
  {
    "rubric_id": "synthesis",
    "rubric_content": {
      "text_property": "Agent synthesizes results before responding."
    }
  }
]
```

#### API Integration

```json
"rubrics": [
  {
    "rubric_id": "authentication",
    "rubric_content": {
      "text_property": "Agent authenticates before API calls."
    }
  },
  {
    "rubric_id": "rate_limiting",
    "rubric_content": {
      "text_property": "Agent handles rate limiting appropriately."
    }
  },
  {
    "rubric_id": "retry_logic",
    "rubric_content": {
      "text_property": "Agent retries failed requests."
    }
  }
]
```

## Part 4: Hallucination Detection

### What is Hallucination Detection?

**Metric**: `hallucinations_v1`

**Detects**: When an agent makes claims NOT supported by:
- Tool outputs
- System instructions
- User-provided context

### How It Works

1. **Split response** into sentences
2. **Evaluate each sentence** against available context
3. **Label sentences**:
   - `SUPPORTED`: Backed by evidence
   - `UNSUPPORTED`: No evidence found
   - `CONTRADICTORY`: Contradicts evidence
   - `DISPUTED`: Conflicting evidence
   - `NOT_APPLICABLE`: Not a factual claim

4. **Calculate score**:
   ```
   Score = (SUPPORTED + NOT_APPLICABLE) / Total Sentences
   ```

### Configuration

```json
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
```

**Parameters**:
- `threshold`: Minimum score to pass (0.0-1.0)
- `judge_model`: LLM model for evaluation
- `evaluate_intermediate_nl_responses`: Check intermediate responses too

### Examples

#### Example 1: No Hallucinations

**Tool Output**:
```json
{"product": "Laptop X", "price": 999, "stock": 5}
```

**Agent Response**:
```
"The Laptop X costs $999 and we have 5 in stock."
```

**Evaluation**:
- "The Laptop X costs $999" → `SUPPORTED`
- "we have 5 in stock" → `SUPPORTED`

**Score**: 2/2 = 1.0 ✓ (no hallucinations)

#### Example 2: With Hallucinations

**Tool Output**:
```json
{"product": "Laptop X", "price": 999, "stock": 5}
```

**Agent Response**:
```
"The Laptop X costs $899 and includes free shipping."
```

**Evaluation**:
- "The Laptop X costs $899" → `CONTRADICTORY` (price is $999!)
- "includes free shipping" → `UNSUPPORTED` (no evidence)

**Score**: 0/2 = 0.0 ✗ (hallucinations detected!)

### When to Use

- Factual accuracy is critical
- Agent has access to specific data
- Financial or medical information
- Legal or compliance contexts
- Customer service (product information)

## Part 5: Safety Evaluation

### What is Safety Evaluation?

**Metric**: `safety_v1`

**Evaluates**: If agent responses are safe and appropriate

### What It Checks

- Hate speech or discrimination
- Harassment or threats
- Dangerous information
- Inappropriate content
- Privacy violations
- Illegal activities

### Configuration

```json
{
  "criteria": {
    "safety_v1": 0.8
  }
}
```

### Requirements

**Note**: Requires Google Cloud Project

Set environment variables:
```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
```

### When to Use

- User-facing applications
- Public deployments
- Sensitive domains
- Compliance requirements
- Children's applications

## Part 6: Sample Banking Agent

The exercise creates a banking agent to demonstrate custom evaluation:

```python
def create_banking_agent():
    agent = LlmAgent(
        name="BankingAgent",
        model="gemini-2.0-flash",
        instruction="""You are a banking assistant.

        IMPORTANT RULES:
        1. Always verify account exists before transfers
        2. Never disclose full account numbers
        3. Confirm transaction details before executing
        4. Be professional and security-conscious
        5. Do not provide financial advice""",
        tools=[balance_tool, transfer_tool, history_tool]
    )
    return agent
```

### Tools

1. **get_account_balance(account_id)**: Get account balance
2. **transfer_funds(from_account, to_account, amount)**: Transfer money
3. **get_transaction_history(account_id, limit)**: Get recent transactions

## Part 7: Complete Configuration Example

### Full Evaluation Configuration

```json
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
```

## Part 8: Rubric Writing Best Practices

### 1. Be Specific

❌ **Bad**: "The response is good"
✓ **Good**: "The response includes the account balance in dollars"

### 2. Make It Evaluable

❌ **Bad**: "The response feels professional"
✓ **Good**: "The response uses formal language and avoids slang"

### 3. One Concept Per Rubric

❌ **Bad**: "The response is accurate and concise"
✓ **Good**: Split into two:
- "The response contains accurate information"
- "The response is under 3 sentences"

### 4. Avoid Ambiguity

❌ **Bad**: "The response is short"
✓ **Good**: "The response is 50 words or fewer"

### 5. Test Your Rubrics

1. Run with known good/bad responses
2. Check if rubric scores match expectations
3. Adjust wording if needed

### 6. Use Domain Language

- **Banking**: "complies with KYC requirements"
- **Medical**: "includes appropriate disclaimers"
- **Legal**: "cites relevant precedents"

### 7. Prioritize Rubrics

Set thresholds based on importance:
- **Safety rubrics**: threshold 0.95+
- **Accuracy rubrics**: threshold 0.85+
- **Style rubrics**: threshold 0.7+

### Rubric Template

```json
{
  "rubric_id": "unique_identifier",      // snake_case
  "rubric_content": {
    "text_property": "Clear yes/no statement about the response."
  }
}
```

## Running the Exercise

```bash
# Navigate to lab5
cd lab5_evaluation

# Run the exercise
uv run python 04_custom_evaluators.py
```

## Expected Output

The exercise will:
1. Explain rubric-based evaluation concepts
2. Show response quality rubric examples
3. Show tool use quality rubric examples
4. Explain hallucination detection
5. Explain safety evaluation
6. Run banking agent demo
7. Show complete configuration
8. Provide rubric writing best practices

## Key Takeaways

### Custom Evaluation Metrics

1. **rubric_based_final_response_quality_v1**
   - Evaluates response quality with custom rubrics
   - Use for: tone, style, completeness, domain criteria

2. **rubric_based_tool_use_quality_v1**
   - Evaluates tool usage patterns with custom rubrics
   - Use for: workflow validation, order of operations

3. **hallucinations_v1**
   - Detects unsupported or contradictory claims
   - Use for: factual accuracy, data integrity

4. **safety_v1**
   - Checks for harmful content
   - Use for: user-facing apps, compliance

### Rubric Structure

```json
{
  "rubric_id": "unique_id",
  "rubric_content": {
    "text_property": "Clear yes/no statement"
  }
}
```

### Best Practices

- **Be specific** and evaluable in rubric wording
- **One concept** per rubric
- **Test rubrics** with known examples
- **Combine metrics** for comprehensive evaluation
- **High thresholds** for safety-critical rubrics

## Next Steps

- **Exercise 5**: Use user simulation for dynamic conversational testing
