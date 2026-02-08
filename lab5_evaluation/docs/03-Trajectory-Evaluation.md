# Exercise 3: Trajectory Evaluation

## Overview

This exercise covers tool trajectory evaluation, which validates that agents use the right tools in the correct way to accomplish tasks.

**File**: `03_trajectory_evaluation.py`

## Learning Objectives

1. Understand what trajectory evaluation measures
2. Master the three match types: EXACT, IN_ORDER, ANY_ORDER
3. Evaluate tool arguments correctly
4. Identify common trajectory patterns
5. Debug trajectory evaluation failures

## Part 1: What is Trajectory Evaluation?

### Definition

**Trajectory** = The sequence of tools an agent calls to complete a task

### Why Evaluate Trajectory?

1. **Workflow validation**: Ensures agent follows expected process
2. **Tool selection**: Verifies correct tools are chosen
3. **Parameter accuracy**: Checks arguments are correct
4. **Efficiency**: Identifies unnecessary or redundant calls

### Example

**User Query**: "What's the weather in NYC and convert it to Celsius?"

**Expected Trajectory**:
```python
[
    {"name": "get_weather", "args": {"city": "New York"}},
    {"name": "fahrenheit_to_celsius", "args": {"temp": 72}}
]
```

**What Gets Evaluated**:

| Aspect | Evaluated? | Notes |
|--------|------------|-------|
| Tool name | ✓ | Must match exactly |
| Tool arguments | ✓ | Key-value pairs checked |
| Tool order | ✓ or - | Depends on match_type |
| Extra tools | ✓ or - | Depends on match_type |
| Tool response | ✗ | Only inputs matter |

## Part 2: Match Types

### 1. EXACT (Default, Strictest)

**Requirements**:
- All expected tools must be called
- In the exact order specified
- With the exact arguments
- NO extra tools allowed

**Example**:
```python
Expected: [tool_a(x=1), tool_b(y=2)]

✓ PASS:  [tool_a(x=1), tool_b(y=2)]
✗ FAIL:  [tool_a(x=1), tool_c(), tool_b(y=2)]  # Extra tool
✗ FAIL:  [tool_b(y=2), tool_a(x=1)]            # Wrong order
✗ FAIL:  [tool_a(x=1)]                          # Missing tool
```

**Configuration**:
```json
{
  "criteria": {
    "tool_trajectory_avg_score": {
      "threshold": 1.0,
      "match_type": "EXACT"
    }
  }
}
```

**Use Cases**:
- Strict workflows (e.g., payments)
- Security-critical operations
- Compliance requirements
- Regression testing

### 2. IN_ORDER (Medium Strictness)

**Requirements**:
- All expected tools must be called
- In the specified order
- With matching arguments
- Extra tools between expected ones are OK

**Example**:
```python
Expected: [tool_a(x=1), tool_b(y=2)]

✓ PASS:  [tool_a(x=1), tool_b(y=2)]
✓ PASS:  [tool_a(x=1), tool_c(), tool_b(y=2)]  # Extra OK
✗ FAIL:  [tool_b(y=2), tool_a(x=1)]            # Wrong order
✗ FAIL:  [tool_a(x=1)]                          # Missing tool
```

**Configuration**:
```json
{
  "criteria": {
    "tool_trajectory_avg_score": {
      "threshold": 1.0,
      "match_type": "IN_ORDER"
    }
  }
}
```

**Use Cases**:
- Ordered pipelines (data processing)
- Multi-step workflows with optional steps
- When agent might retry or explore

### 3. ANY_ORDER (Most Flexible)

**Requirements**:
- All expected tools must be called
- Order doesn't matter
- With matching arguments
- Extra tools are OK

**Example**:
```python
Expected: [tool_a(x=1), tool_b(y=2)]

✓ PASS:  [tool_a(x=1), tool_b(y=2)]
✓ PASS:  [tool_b(y=2), tool_a(x=1)]            # Order OK
✓ PASS:  [tool_a(x=1), tool_c(), tool_b(y=2)]  # Extra OK
✗ FAIL:  [tool_a(x=1)]                          # Missing tool
✗ FAIL:  [tool_a(x=2), tool_b(y=2)]            # Wrong args
```

**Configuration**:
```json
{
  "criteria": {
    "tool_trajectory_avg_score": {
      "threshold": 1.0,
      "match_type": "ANY_ORDER"
    }
  }
}
```

**Use Cases**:
- Flexible tool gathering (research)
- Multiple search queries
- Parallel operations
- When order doesn't matter

### Match Type Decision Matrix

| Requirement | EXACT | IN_ORDER | ANY_ORDER |
|-------------|-------|----------|-----------|
| Exact tool sequence | ✓ | ✓ | - |
| Allows extra tools | - | ✓ | ✓ |
| Order flexibility | - | - | ✓ |
| Strictest | ✓ | - | - |
| Most flexible | - | - | ✓ |

## Part 3: Sample Shopping Agent

The exercise creates a shopping agent with multiple tools:

```python
def create_shopping_agent():
    agent = LlmAgent(
        name="ShoppingAgent",
        model="gemini-2.0-flash",
        instruction="""You are a shopping assistant.

        Workflow for product inquiries:
        1. Search for products using search_products
        2. Get details with get_product_details
        3. Check availability with check_inventory

        For purchases:
        1. First check inventory
        2. Then add to cart""",
        tools=[search_tool, details_tool, inventory_tool, cart_tool]
    )
    return agent
```

### Tools

1. **search_products(query, category)**
   - Search for products by keyword
   - Returns list of matching products

2. **get_product_details(product_id)**
   - Get detailed product information
   - Returns specs, price, description

3. **check_inventory(product_id)**
   - Check product availability
   - Returns in_stock status and quantity

4. **add_to_cart(product_id, quantity)**
   - Add product to shopping cart
   - Returns success message

## Part 4: Trajectory Matching Simulation

### Expected Trajectory

```python
expected = [
    {"name": "search_products", "args": {"query": "laptop"}},
    {"name": "get_product_details", "args": {"product_id": "P001"}},
    {"name": "check_inventory", "args": {"product_id": "P001"}}
]
```

### Test Cases

#### Case 1: Exact Match
```python
actual = [
    {"name": "search_products", "args": {"query": "laptop"}},
    {"name": "get_product_details", "args": {"product_id": "P001"}},
    {"name": "check_inventory", "args": {"product_id": "P001"}}
]

EXACT:     ✓ PASS
IN_ORDER:  ✓ PASS
ANY_ORDER: ✓ PASS
```

#### Case 2: Extra Tool in Between
```python
actual = [
    {"name": "search_products", "args": {"query": "laptop"}},
    {"name": "search_products", "args": {"query": "gaming laptop"}},  # Extra
    {"name": "get_product_details", "args": {"product_id": "P001"}},
    {"name": "check_inventory", "args": {"product_id": "P001"}}
]

EXACT:     ✗ FAIL (extra tool not allowed)
IN_ORDER:  ✓ PASS (extra tool between expected ones)
ANY_ORDER: ✓ PASS (extra tools OK)
```

#### Case 3: Wrong Order
```python
actual = [
    {"name": "search_products", "args": {"query": "laptop"}},
    {"name": "check_inventory", "args": {"product_id": "P001"}},  # Swapped
    {"name": "get_product_details", "args": {"product_id": "P001"}}
]

EXACT:     ✗ FAIL (wrong order)
IN_ORDER:  ✗ FAIL (wrong order)
ANY_ORDER: ✓ PASS (order doesn't matter)
```

#### Case 4: Missing Tool
```python
actual = [
    {"name": "search_products", "args": {"query": "laptop"}},
    {"name": "check_inventory", "args": {"product_id": "P001"}}
    # Missing get_product_details
]

EXACT:     ✗ FAIL (missing tool)
IN_ORDER:  ✗ FAIL (missing tool)
ANY_ORDER: ✗ FAIL (missing tool)
```

#### Case 5: Wrong Argument
```python
actual = [
    {"name": "search_products", "args": {"query": "phone"}},  # Wrong query!
    {"name": "get_product_details", "args": {"product_id": "P001"}},
    {"name": "check_inventory", "args": {"product_id": "P001"}}
]

EXACT:     ✗ FAIL (wrong argument)
IN_ORDER:  ✗ FAIL (wrong argument)
ANY_ORDER: ✗ FAIL (wrong argument)
```

## Part 5: Evaluation Logic

### Simplified Algorithm

```python
def evaluate_trajectory(expected, actual, match_type):
    def tools_match(exp, act):
        """Check if two tool calls match."""
        if exp['name'] != act['name']:
            return False
        for key, value in exp['args'].items():
            if key not in act['args'] or act['args'][key] != value:
                return False
        return True

    if match_type == 'EXACT':
        # Must be exact match: same tools, same order, no extras
        if len(expected) != len(actual):
            return False
        for exp, act in zip(expected, actual):
            if not tools_match(exp, act):
                return False
        return True

    elif match_type == 'IN_ORDER':
        # Expected tools must appear in order, extras allowed
        exp_idx = 0
        for act in actual:
            if exp_idx < len(expected) and tools_match(expected[exp_idx], act):
                exp_idx += 1
        return exp_idx == len(expected)

    elif match_type == 'ANY_ORDER':
        # All expected tools must appear, any order, extras allowed
        matched = [False] * len(expected)
        for act in actual:
            for i, exp in enumerate(expected):
                if not matched[i] and tools_match(exp, act):
                    matched[i] = True
                    break
        return all(matched)
```

## Part 6: Configuration Examples

### Basic (EXACT, Default)

```json
{
  "criteria": {
    "tool_trajectory_avg_score": 1.0
  }
}
```

### Explicit EXACT

```json
{
  "criteria": {
    "tool_trajectory_avg_score": {
      "threshold": 1.0,
      "match_type": "EXACT"
    }
  }
}
```

### IN_ORDER (Allows Extras)

```json
{
  "criteria": {
    "tool_trajectory_avg_score": {
      "threshold": 1.0,
      "match_type": "IN_ORDER"
    }
  }
}
```

### ANY_ORDER (Flexible)

```json
{
  "criteria": {
    "tool_trajectory_avg_score": {
      "threshold": 1.0,
      "match_type": "ANY_ORDER"
    }
  }
}
```

### Combined with Response Evaluation

```json
{
  "criteria": {
    "tool_trajectory_avg_score": {
      "threshold": 0.9,
      "match_type": "IN_ORDER"
    },
    "response_match_score": 0.8
  }
}
```

## Part 7: Test File Format

### Trajectory in Test File

```json
{
  "intermediate_data": {
    "tool_uses": [
      {
        "name": "search_products",
        "args": {"query": "laptop"}
      },
      {
        "name": "get_product_details",
        "args": {"product_id": "P001"}
      }
    ],
    "intermediate_responses": []
  }
}
```

### Complete Test Case

```json
{
  "eval_id": "product_search",
  "conversation": [
    {
      "user_content": {
        "parts": [{"text": "Find me a laptop"}]
      },
      "final_response": {
        "parts": [{"text": "I found the Pro Laptop for $1299."}]
      },
      "intermediate_data": {
        "tool_uses": [
          {"name": "search_products", "args": {"query": "laptop"}},
          {"name": "get_product_details", "args": {"product_id": "P001"}}
        ]
      }
    }
  ]
}
```

## Part 8: Debugging Tips

### 1. Tool Name Mismatch

**Problem**:
```
Expected: "get_weather"
Actual:   "getWeather"
```

**Solution**: Check exact function names in tool definitions

### 2. Argument Mismatch

**Problem**:
```
Expected: {"city": "New York"}
Actual:   {"city": "NYC"}
```

**Solutions**:
- Update expected args to match likely variations
- Normalize inputs in tool function
- Use ANY_ORDER if argument variations are acceptable

### 3. Missing Tools

**Problem**:
```
Expected: [search, details, inventory]
Actual:   [search, inventory]  # Missing details
```

**Solutions**:
- Check agent instruction clarity
- Verify tool descriptions are clear
- Review if expected trajectory is realistic

### 4. Extra Tools (Retries/Exploration)

**Problem**:
```
Expected: [search]
Actual:   [search, search, search]  # Agent retrying
```

**Solutions**:
- Use `IN_ORDER` or `ANY_ORDER` if retries are acceptable
- Adjust agent instruction to minimize retries
- Consider if retries indicate a problem

### 5. Wrong Order

**Problem**:
```
Expected: [check_inventory, add_to_cart]
Actual:   [add_to_cart, check_inventory]  # Reversed!
```

**Solutions**:
- Make workflow clearer in agent instruction
- Use numbered steps in instruction
- Consider if order really matters (maybe use ANY_ORDER)

### Debugging Commands

```bash
# Run with detailed output
adk eval my_agent tests/ --print_detailed_results

# Use pytest for better debugging
pytest tests/ -v --tb=long
```

### Debugging Strategy

1. **Start with ANY_ORDER** - See if all tools are called correctly
2. **Move to IN_ORDER** - Verify sequencing
3. **Use EXACT** - Ensure no extras

## Running the Exercise

```bash
# Navigate to lab5
cd lab5_evaluation

# Run the exercise
uv run python 03_trajectory_evaluation.py
```

## Expected Output

The exercise will:
1. Explain trajectory evaluation concepts
2. Demonstrate the three match types
3. Create a shopping agent
4. Simulate trajectory matching with different scenarios
5. Run live trajectory capture
6. Show configuration examples
7. Provide debugging tips

## Key Takeaways

### Trajectory Evaluation Basics

- **Trajectory** = sequence of tool calls
- Evaluates tool selection, order, and arguments
- Three match types for different strictness levels

### Match Types

| Type | Strictness | Use Case |
|------|------------|----------|
| EXACT | Highest | Critical workflows |
| IN_ORDER | Medium | Ordered pipelines |
| ANY_ORDER | Lowest | Flexible gathering |

### Configuration

```json
{
  "criteria": {
    "tool_trajectory_avg_score": {
      "threshold": 1.0,
      "match_type": "EXACT"  // or "IN_ORDER" or "ANY_ORDER"
    }
  }
}
```

### Best Practices

1. **Choose match type** based on workflow requirements
2. **Use EXACT** for critical workflows (payments, security)
3. **Use ANY_ORDER** for flexible operations (research, search)
4. **Check both tool names AND arguments**
5. **Start flexible, tighten as needed**

## Next Steps

- **Exercise 4**: Create custom rubrics for domain-specific evaluation
- **Exercise 5**: Use user simulation for dynamic conversations
