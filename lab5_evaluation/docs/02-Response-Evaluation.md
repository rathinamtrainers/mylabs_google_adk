# Exercise 2: Response Evaluation

## Overview

This exercise covers response quality evaluation techniques, comparing word-based matching (ROUGE-1) with semantic matching (LLM-as-judge).

**File**: `02_response_evaluation.py`

## Learning Objectives

1. Understand ROUGE-1 word overlap scoring
2. Learn semantic matching with LLM-as-judge
3. Compare lexical vs semantic approaches
4. Set appropriate evaluation thresholds
5. Write effective reference responses

## Part 1: Two Approaches to Response Evaluation

### 1. Lexical Matching: response_match_score

**Method**: ROUGE-1 (word overlap)

**Characteristics**:
- Fast and deterministic
- Counts overlapping words
- No understanding of meaning

**Best for**:
- CI/CD automated tests
- Quick regression checks
- When exact wording matters

**Limitation**: Misses semantic equivalence

### 2. Semantic Matching: final_response_match_v2

**Method**: LLM-as-judge

**Characteristics**:
- Understands meaning
- Slower, costs more
- Handles paraphrasing

**Best for**:
- Quality assessment
- Flexible output formats
- Multiple valid answers

**Limitation**: Non-deterministic, more expensive

## Part 2: ROUGE-1 Scoring

### What is ROUGE-1?

ROUGE-1 (Recall-Oriented Understudy for Gisting Evaluation) measures **unigram overlap** between two texts.

### How It Works

```python
def calculate_rouge1_score(reference: str, candidate: str):
    # Tokenize into words
    ref_words = set(reference.lower().split())
    cand_words = set(candidate.lower().split())

    # Find overlap
    overlap = ref_words.intersection(cand_words)

    # Calculate metrics
    precision = len(overlap) / len(cand_words)
    recall = len(overlap) / len(ref_words)
    f1 = 2 * (precision * recall) / (precision + recall)

    return {"precision": precision, "recall": recall, "f1": f1}
```

### Metrics Explained

#### Precision
**What % of candidate words are in reference?**

```
Reference: "The result is 42"
Candidate: "The answer is 42"

Overlap: {the, is, 42}
Precision: 3/4 = 0.75 (75% of candidate words match)
```

#### Recall
**What % of reference words are in candidate?**

```
Reference: "The result is 42"
Candidate: "The answer is 42"

Overlap: {the, is, 42}
Recall: 3/4 = 0.75 (75% of reference words found)
```

#### F1 Score
**Harmonic mean of precision and recall**

```
F1 = 2 * (precision * recall) / (precision + recall)
F1 = 2 * (0.75 * 0.75) / (0.75 + 0.75)
F1 = 0.75
```

### Examples

#### Example 1: Exact Match
```
Reference: "The result is 42"
Candidate: "The result is 42"

Overlap: {the, result, is, 42}
F1: 1.0 (perfect match)
```

#### Example 2: Same Words, Different Order
```
Reference: "The result is 42"
Candidate: "42 is the result"

Overlap: {the, result, is, 42}
F1: 1.0 (order doesn't matter)
```

#### Example 3: Same Meaning, Different Words
```
Reference: "The temperature is 72 degrees Fahrenheit"
Candidate: "It's 72°F outside"

Overlap: {72}
F1: ~0.15 (low score despite same meaning!)
```

#### Example 4: Paraphrase
```
Reference: "The capital of France is Paris"
Candidate: "Paris is the capital city of France"

Overlap: {the, capital, of, france, is, paris}
F1: 0.92 (high score)
```

#### Example 5: Different Wording
```
Reference: "Error: Division by zero"
Candidate: "Cannot divide by zero"

Overlap: {by, zero}
F1: 0.44 (moderate score)
```

### Configuration

```json
{
  "criteria": {
    "response_match_score": 0.8
  }
}
```

**Threshold Guidelines**:
- `1.0`: Perfect match (usually too strict)
- `0.8`: High similarity (recommended default)
- `0.6`: Moderate similarity
- `0.4`: Low similarity

## Part 3: Semantic Matching

### How LLM-as-Judge Works

1. **Send both responses to judge LLM**
   ```
   Judge: Do these responses convey the same information?
   Reference: "The sum of 5 and 3 is 8"
   Candidate: "5 + 3 = 8"
   ```

2. **Judge returns verdict**
   - VALID: Same meaning
   - INVALID: Different meaning

3. **Repeat for robustness**
   - Run multiple times (`num_samples`)
   - Use majority vote

4. **Calculate score**
   - Score = VALID votes / total samples

### Configuration

```json
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
```

**Parameters**:
- `threshold`: Minimum score to pass (0.0-1.0)
- `judge_model`: LLM model to use as judge
- `num_samples`: How many times to evaluate (for consistency)

### What the Judge Considers

✓ **Accepts**:
- Same core information
- Different phrasing
- Additional correct details
- Equivalent representations

✗ **Rejects**:
- Missing key information
- Contradictory statements
- Factually incorrect additions
- Incomplete answers

### Examples

#### Example 1: Different Format
```
Reference: "The sum of 5 and 3 is 8"
Candidate: "5 + 3 = 8"
Result: VALID (same information)
```

#### Example 2: Extra Details
```
Reference: "The capital of France is Paris"
Candidate: "Paris, located in France, is the capital"
Result: VALID (extra detail is correct)
```

#### Example 3: Contradictory
```
Reference: "The result is 42"
Candidate: "The result is 24"
Result: INVALID (different numbers)
```

#### Example 4: Missing Information
```
Reference: "The weather is 72°F and sunny"
Candidate: "It's 72°F"
Result: INVALID (missing 'sunny')
```

## Part 4: Sample Weather Agent

The exercise creates a weather agent to demonstrate response evaluation:

```python
def create_weather_agent():
    agent = LlmAgent(
        name="WeatherAgent",
        model="gemini-2.0-flash",
        instruction="""You are a weather assistant.
        When asked about weather, use the get_weather tool.
        Report the temperature, conditions, and humidity.
        Be concise but include all three pieces of information.""",
        tools=[weather_tool]
    )
    return agent
```

### Tool Output
```python
{
    "temp": 72,
    "condition": "sunny",
    "humidity": 45
}
```

### Reference Responses (Multiple Valid)

For "What's the weather in New York?":

1. `"It's 72°F and sunny in New York with 45% humidity."`
2. `"New York: Temperature 72°F, Sunny, Humidity 45%"`
3. `"The weather in New York is sunny with a temperature of 72 degrees and humidity at 45 percent."`

All are valid variations that should score high on semantic matching but may differ on ROUGE-1.

## Part 5: Comparison Matrix

### When to Use Each Metric

| Scenario | ROUGE-1 | Semantic |
|----------|---------|----------|
| CI/CD automated tests | ✓ | - |
| Quick regression checks | ✓ | - |
| Quality assessment | - | ✓ |
| Flexible output formats | - | ✓ |
| Multiple valid answers | - | ✓ |
| Budget-conscious | ✓ | - |
| Understanding meaning | - | ✓ |
| Fast feedback | ✓ | - |

### Example Comparison

```
Reference: "The temperature is 72 degrees Fahrenheit"
Candidate: "It's 72°F"

ROUGE-1 F1: 0.14 (very low)
Semantic: 1.0 (perfect match)
```

## Part 6: Best Practices

### 1. Choose the Right Metric

```json
{
  "criteria": {
    // Fast check for regressions
    "response_match_score": 0.6,

    // Deep semantic check
    "final_response_match_v2": {
      "threshold": 0.8,
      "judge_model_options": {
        "judge_model": "gemini-2.5-flash",
        "num_samples": 3
      }
    }
  }
}
```

### 2. Set Appropriate Thresholds

```
Perfect match (1.0)    ←  Too strict for most cases
Good match (0.8)       ←  Recommended default
Moderate match (0.6)   ←  For flexible outputs
Loose match (0.4)      ←  Too permissive
```

### 3. Write Good Reference Responses

❌ **Bad**: Too specific
```json
"final_response": {
  "parts": [{"text": "The current temperature in New York City, NY is exactly 72 degrees Fahrenheit with sunny conditions and humidity at 45%."}]
}
```

✓ **Good**: Core information
```json
"final_response": {
  "parts": [{"text": "It's 72°F and sunny in New York with 45% humidity."}]
}
```

### 4. Handle Variability

Run multiple evaluations to account for LLM variance:

```python
AgentEvaluator.evaluate(
    agent_module="my_agent",
    eval_dataset_file_path_or_dir="tests/",
    num_runs=3  # Run each test 3 times
)
```

### 5. Combine Metrics

Use both for comprehensive evaluation:

```json
{
  "criteria": {
    "response_match_score": 0.6,           // Baseline word overlap
    "final_response_match_v2": {           // Semantic check
      "threshold": 0.8
    }
  }
}
```

### 6. Test File Organization

```
my_agent/
├── agent.py
├── test_config.json          # Evaluation criteria
└── tests/
    ├── basic.test.json       # Basic functionality
    ├── edge_cases.test.json  # Edge cases
    └── multi_turn.test.json  # Multi-turn conversations
```

## Running the Exercise

```bash
# Navigate to lab5
cd lab5_evaluation

# Run the exercise
uv run python 02_response_evaluation.py
```

## Expected Output

The exercise will:
1. Explain response evaluation approaches
2. Demonstrate ROUGE-1 scoring with examples
3. Explain semantic matching concepts
4. Run weather agent to generate responses
5. Simulate evaluation against reference responses
6. Show best practices

## Key Takeaways

### Response Evaluation Metrics

1. **response_match_score (ROUGE-1)**
   - Measures word overlap
   - Fast and deterministic
   - Best for CI/CD
   - Config: `{"response_match_score": 0.8}`

2. **final_response_match_v2 (LLM-as-Judge)**
   - Measures semantic similarity
   - Understands meaning
   - Best for quality assessment
   - Config: See configuration section above

### Key Insights

- **ROUGE-1** is fast but misses semantic similarity
- **LLM-as-judge** is slower but understands meaning
- Use **appropriate thresholds** (0.8 is a good default)
- **Combine both** for comprehensive evaluation
- Write reference responses with **core info**, not exact phrasing

## Comparison Table

| Aspect | ROUGE-1 | Semantic |
|--------|---------|----------|
| **Speed** | Fast (ms) | Slow (seconds) |
| **Cost** | Free | LLM API calls |
| **Deterministic** | Yes | No |
| **Understands meaning** | No | Yes |
| **Handles paraphrasing** | No | Yes |
| **CI/CD friendly** | Yes | No |
| **Accuracy** | Medium | High |

## Next Steps

- **Exercise 3**: Learn trajectory evaluation (tool usage patterns)
- **Exercise 4**: Create custom rubrics for domain-specific criteria
- **Exercise 5**: Use user simulation for dynamic conversations
