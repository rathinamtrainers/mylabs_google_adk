# Exercise 5: User Simulation

## Overview

This exercise covers dynamic user simulation for testing conversational agents with flexible, multi-turn interactions.

**File**: `05_user_simulation.py`

## Learning Objectives

1. Understand why user simulation is necessary
2. Create conversation scenarios
3. Configure the user simulator
4. Understand supported metrics
5. Apply user simulation best practices

## Part 1: Why User Simulation?

### The Problem with Fixed Test Cases

Fixed test cases break with dynamic conversations.

#### Scenario: Agent Needs User Email and Phone

**Case 1**: Agent asks both at once
```
Agent: "Please provide your email and phone number."
User: ??? (your fixed test didn't expect this)
```

**Case 2**: Agent asks one at a time
```
Agent: "What's your email?"
User: "user@example.com"
Agent: "What's your phone number?"
User: ??? (different flow than Case 1)
```

**Problem**: You can't predict the exact conversation flow!

### The Solution: User Simulation

**User Simulation** = An LLM plays the role of the user

Instead of fixed prompts, you define:
- **Starting prompt**: First message to send
- **Conversation plan**: What the user wants to achieve

The simulator LLM:
1. Reads the agent's responses
2. Generates appropriate user messages
3. Follows the conversation plan
4. Decides when conversation is complete

### Benefits

1. **Handles dynamic behavior**: Adapts to agent's responses
2. **Tests real flows**: Validates actual conversation patterns
3. **More realistic**: Closer to production usage
4. **Catches edge cases**: Discovers unexpected paths

### Limitations

1. **No reference comparison**: Can't compare against expected trajectory/response
2. **Limited metrics**: Only hallucinations_v1 and safety_v1 supported
3. **LLM cost**: Simulator uses LLM API calls
4. **Non-deterministic**: Different runs may take different paths

## Part 2: Conversation Scenarios

### ConversationScenario Structure

```json
{
  "starting_prompt": "The first message to send",
  "conversation_plan": "Description of what user wants to achieve"
}
```

### Example Scenarios

#### Simple Task

```json
{
  "starting_prompt": "Hi, I need help",
  "conversation_plan": "Ask the agent to find a flight from NYC to LA for next Friday."
}
```

#### Multi-Step Task

```json
{
  "starting_prompt": "I want to make a purchase",
  "conversation_plan": "Search for laptops under $1000. Ask about the cheapest option's specs. If it looks good, add it to cart."
}
```

#### Information Gathering

```json
{
  "starting_prompt": "What can you help me with?",
  "conversation_plan": "Ask the agent about its capabilities. Then ask it to demonstrate one feature with a simple example."
}
```

#### Challenging Scenario

```json
{
  "starting_prompt": "I'm frustrated with your service!",
  "conversation_plan": "Express dissatisfaction about a previous order. See how the agent handles complaints and if it offers a resolution."
}
```

### Scenarios File Format

**File**: `conversation_scenarios.json`

```json
{
  "scenarios": [
    {
      "starting_prompt": "...",
      "conversation_plan": "..."
    },
    {
      "starting_prompt": "...",
      "conversation_plan": "..."
    }
  ]
}
```

## Part 3: Setting Up User Simulation

### Step 1: Create Scenarios File

**File**: `my_agent/conversation_scenarios.json`

```json
{
  "scenarios": [
    {
      "starting_prompt": "Hello, I need to book a flight",
      "conversation_plan": "Book a round-trip flight from New York to Los Angeles. Departure on December 15th, return on December 22nd. Prefer economy class."
    },
    {
      "starting_prompt": "What flights are available?",
      "conversation_plan": "Ask about same-day flights to Chicago. Accept the cheapest option if under $300, otherwise decline."
    }
  ]
}
```

### Step 2: Create Session Input File

**File**: `my_agent/session_input.json`

```json
{
  "app_name": "flight_booking_agent",
  "user_id": "test_user"
}
```

### Step 3: Create Eval Set with Scenarios

```bash
# Create eval set
adk eval_set create my_agent my_eval_set

# Add eval case with scenarios
adk eval_set add_eval_case \
  my_agent \
  my_eval_set \
  --scenarios_file my_agent/conversation_scenarios.json \
  --session_input_file my_agent/session_input.json
```

### Step 4: Create Eval Config

**File**: `my_agent/eval_config.json`

```json
{
  "criteria": {
    "hallucinations_v1": {
      "threshold": 0.8,
      "evaluate_intermediate_nl_responses": true
    },
    "safety_v1": {
      "threshold": 0.9
    }
  }
}
```

### Step 5: Run Evaluation

```bash
adk eval \
  my_agent \
  --config_file_path my_agent/eval_config.json \
  my_eval_set \
  --print_detailed_results
```

### Important Note

**Reference-based metrics NOT supported** with user simulation:
- ✗ `tool_trajectory_avg_score`
- ✗ `response_match_score`
- ✗ `final_response_match_v2`

**Reason**: Dynamic conversations mean unpredictable trajectories and responses.

## Part 4: User Simulator Configuration

### Full Configuration

```json
{
  "criteria": {
    "hallucinations_v1": {"threshold": 0.8},
    "safety_v1": 0.9
  },
  "user_simulator_config": {
    "model": "gemini-2.5-flash",
    "model_configuration": {
      "thinking_config": {
        "include_thoughts": true,
        "thinking_budget": 10240
      }
    },
    "max_allowed_invocations": 20
  }
}
```

### Configuration Options

#### model (string)

**Description**: The LLM model for user simulation

**Default**: `"gemini-2.5-flash"`

**Options**: Any Gemini model

**Example**:
```json
"model": "gemini-2.5-flash"
```

#### model_configuration (GenerateContentConfig)

**Description**: Controls model behavior

**Options**:
- `thinking_config`: Enable reasoning
- `temperature`: Creativity level
- Other generation parameters

**Example**:
```json
"model_configuration": {
  "thinking_config": {
    "include_thoughts": true,
    "thinking_budget": 10240
  },
  "temperature": 0.7
}
```

#### max_allowed_invocations (int)

**Description**: Maximum user-agent turns

**Default**: `20`

**Purpose**: Prevents infinite conversations

**Guidance**:
- Simple tasks: 5-10
- Medium complexity: 10-15
- Complex multi-step: 15-25

**Example**:
```json
"max_allowed_invocations": 20
```

### Thinking Config

The simulator can "think" about what to say next:

```json
"thinking_config": {
  "include_thoughts": true,    // Enable reasoning
  "thinking_budget": 10240     // Token budget for thinking
}
```

**Benefits**:
- Better follows conversation plan
- Makes more realistic decisions
- Determines when conversation is complete

## Part 5: Sample Flight Agent

The exercise creates a flight booking agent:

```python
def create_flight_agent():
    agent = LlmAgent(
        name="FlightAgent",
        model="gemini-2.0-flash",
        instruction="""You are a flight booking assistant.

        Workflow:
        1. Ask for origin, destination, and date
        2. Search for available flights
        3. Help customer choose a flight
        4. Collect passenger name and email
        5. Book the flight
        6. Provide confirmation number

        Ask for one piece of information at a time.""",
        tools=[search_tool, book_tool, cancel_tool]
    )
    return agent
```

### Tools

1. **search_flights(origin, destination, date)**: Search for flights
2. **book_flight(flight_id, passenger_name, email)**: Book a flight
3. **cancel_booking(confirmation_number)**: Cancel booking

### Example Conversation

```
User: "Hi, I need to book a flight"
Agent: "I'd be happy to help! Where are you flying from?"

User: "I want to fly from New York to Los Angeles on December 15th"
Agent: "Great! I found 3 flights: [lists options]. Which would you prefer?"

User: "I'll take the cheapest one, FL003"
Agent: "Perfect! May I have your name for the booking?"

User: "My name is John Smith and my email is john@example.com"
Agent: "Booked! Your confirmation is CONF-FL003-001."
```

## Part 6: Supported Metrics

### Metrics Compatible with User Simulation

#### ✓ hallucinations_v1

**Why**: Checks if agent makes unsupported claims

**Works because**:
- Evaluates agent output vs context
- No expected response needed
- Validates factual accuracy

**Configuration**:
```json
"hallucinations_v1": {
  "threshold": 0.8,
  "evaluate_intermediate_nl_responses": true
}
```

#### ✓ safety_v1

**Why**: Checks if agent output is safe

**Works because**:
- Evaluates agent responses only
- No expected response needed
- Validates appropriateness

**Configuration**:
```json
"safety_v1": 0.9
```

### Metrics NOT Supported

#### ✗ tool_trajectory_avg_score

**Why not**: Requires expected tool calls

**Problem**: Dynamic conversation = unpredictable tools

#### ✗ response_match_score

**Why not**: Requires expected response

**Problem**: Dynamic conversation = unpredictable responses

#### ✗ final_response_match_v2

**Why not**: Requires reference response

**Problem**: Dynamic conversation = no fixed reference

#### ✗ rubric_based_final_response_quality_v1

**Why not**: Currently not supported with simulation

**Status**: May be added in future versions

#### ✗ rubric_based_tool_use_quality_v1

**Why not**: Currently not supported with simulation

**Status**: May be added in future versions

### Recommended Configuration

```json
{
  "criteria": {
    "hallucinations_v1": {
      "threshold": 0.8,
      "evaluate_intermediate_nl_responses": true
    },
    "safety_v1": 0.9
  },
  "user_simulator_config": {
    "model": "gemini-2.5-flash",
    "max_allowed_invocations": 20
  }
}
```

## Part 7: Best Practices

### 1. Write Clear Conversation Plans

❌ **Bad**: "Book a flight"

✓ **Good**: "Book a round-trip flight from NYC to LA. Departure Dec 15, return Dec 22. Prefer economy class under $400."

### 2. Test Edge Cases

Include challenging scenarios:

```json
{
  "starting_prompt": "I need a flight",
  "conversation_plan": "Try to book a flight but change your mind halfway through."
}
```

```json
{
  "starting_prompt": "Can you help me?",
  "conversation_plan": "Ask about something the agent can't do and see how it handles limitations."
}
```

```json
{
  "starting_prompt": "This is frustrating!",
  "conversation_plan": "Express frustration and see how agent responds with empathy."
}
```

### 3. Set Appropriate max_invocations

| Task Complexity | Recommended Value |
|----------------|-------------------|
| Simple tasks | 5-10 |
| Medium complexity | 10-15 |
| Complex multi-step | 15-25 |
| Default | 20 |

### 4. Use Varied Starting Prompts

**Formal**: "I would like to inquire about..."
**Casual**: "Hey, can you help me..."
**Direct**: "Book a flight to NYC"
**Vague**: "I need some travel help"

### 5. Combine Static and Dynamic Tests

```
my_agent/
├── tests/
│   ├── static/               # Fixed test cases
│   │   ├── basic.test.json   # Known inputs/outputs
│   │   └── edge.test.json    # Edge cases
│   └── dynamic/              # User simulation
│       └── conversation_scenarios.json
```

### 6. Monitor Conversation Length

**If hitting max_invocations frequently**:
- Conversation plan may be too complex
- Agent may be getting stuck
- Simulator may be confused

**Solution**: Simplify plan or increase limit

### 7. Review Simulation Transcripts

Run with detailed results:
```bash
adk eval my_agent my_eval_set --print_detailed_results
```

Review:
- Full conversation history
- Where things went wrong
- Unexpected agent behavior

### Example Scenario Set

```json
{
  "scenarios": [
    // Happy path
    {
      "starting_prompt": "Book a flight",
      "conversation_plan": "Complete booking with all valid info"
    },

    // Edge case: Cancellation
    {
      "starting_prompt": "I made a booking",
      "conversation_plan": "Ask to cancel, provide confirmation number"
    },

    // Edge case: Unavailable route
    {
      "starting_prompt": "Fly me to the moon",
      "conversation_plan": "Ask for impossible route, accept agent's limitations gracefully"
    },

    // Stress test: Changing requirements
    {
      "starting_prompt": "I need a flight",
      "conversation_plan": "Start with NYC to LA, then change to Chicago, then back to LA"
    }
  ]
}
```

## Running the Exercise

```bash
# Navigate to lab5
cd lab5_evaluation

# Run the exercise
uv run python 05_user_simulation.py
```

## Expected Output

The exercise will:
1. Explain why user simulation is needed
2. Show conversation scenario structure
3. Demonstrate setup steps
4. Explain simulator configuration
5. Run simulated conversation demo
6. Show supported metrics
7. Provide best practices

## Key Takeaways

### User Simulation Overview

- **LLM plays the user** role, generating dynamic responses
- Define **goals**, not exact messages
- Handles **unpredictable conversation flows**

### Conversation Scenario

```json
{
  "starting_prompt": "First user message",
  "conversation_plan": "Description of user's goal"
}
```

### Setup Steps

1. Create `conversation_scenarios.json` with scenarios
2. Create `session_input.json` with app/user info
3. Add scenarios to eval set: `adk eval_set add_eval_case`
4. Create `eval_config.json` with supported metrics
5. Run: `adk eval my_agent my_eval_set`

### Supported Metrics

✓ **hallucinations_v1** - Fact checking
✓ **safety_v1** - Safety checking
✗ **tool_trajectory_*** - Not supported
✗ **response_match_*** - Not supported

### Simulator Config

```json
{
  "user_simulator_config": {
    "model": "gemini-2.5-flash",
    "max_allowed_invocations": 20
  }
}
```

### Best Practices

1. Write **clear conversation plans**
2. Test **edge cases**
3. Set **appropriate max_invocations**
4. Use **varied starting prompts**
5. **Combine** static and dynamic tests
6. **Review transcripts** to debug

## Comparison: Static vs Dynamic Testing

| Aspect | Static Tests | Dynamic Tests (Simulation) |
|--------|--------------|----------------------------|
| **Predictability** | High | Low |
| **Flexibility** | Low | High |
| **Maintenance** | High effort | Low effort |
| **Coverage** | Specific paths | Realistic flows |
| **Metrics** | All supported | Limited (hallucinations, safety) |
| **Use case** | Regression tests | Exploratory testing |
| **Best for** | Known scenarios | Conversational agents |

### Recommendation

Use **both**:
- **Static tests**: Core functionality, regressions
- **Dynamic tests**: Conversation quality, edge cases

## Next Steps

This concludes Lab 5. You've learned:
1. ✓ Evaluation basics (data structures, running evaluations)
2. ✓ Response evaluation (ROUGE-1, semantic matching)
3. ✓ Trajectory evaluation (EXACT, IN_ORDER, ANY_ORDER)
4. ✓ Custom evaluators (rubrics, hallucination, safety)
5. ✓ User simulation (dynamic conversational testing)

### Related Labs

- **Lab 2**: Sessions & Memory (for stateful agents)
- **Lab 3**: Callbacks & Plugins (for monitoring)
- **Lab 6**: Streaming (for real-time interactions)
