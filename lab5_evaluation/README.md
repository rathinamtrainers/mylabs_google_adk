# Lab 5: Evaluation & Testing

This lab covers agent evaluation in Google ADK:
1. Evaluation fundamentals and concepts
2. Response quality evaluation
3. Tool trajectory evaluation
4. Custom evaluators and rubrics
5. User simulation for dynamic testing

## Prerequisites

```bash
cd /home/agenticai/research_gadk/mylabs/lab5_evaluation
uv init
uv add google-adk pandas tabulate rouge-score
```

## Exercises

| Exercise | Topic | Description |
|----------|-------|-------------|
| 01 | Evaluation Basics | Core concepts, eval sets, running evaluations |
| 02 | Response Evaluation | ROUGE-1 matching, semantic matching |
| 03 | Trajectory Evaluation | Tool use patterns, exact/in-order/any-order matching |
| 04 | Custom Evaluators | Rubric-based evaluation, LLM-as-judge |
| 05 | User Simulation | Dynamic conversation scenarios |

## Running Exercises

```bash
# Set your API key
export GOOGLE_API_KEY="your-api-key"

# Run individual exercises
uv run python 01_evaluation_basics.py
uv run python 02_response_evaluation.py
uv run python 03_trajectory_evaluation.py
uv run python 04_custom_evaluators.py
uv run python 05_user_simulation.py
```

## Key Concepts

### Evaluation Types
- **Response Evaluation**: Did the agent give the right answer?
- **Trajectory Evaluation**: Did the agent use the right tools?
- **Safety Evaluation**: Is the response safe and appropriate?
- **Hallucination Detection**: Is the response grounded in facts?

### Built-in Metrics
- `tool_trajectory_avg_score` - Exact/in-order/any-order tool matching
- `response_match_score` - ROUGE-1 word overlap
- `final_response_match_v2` - LLM-judged semantic matching
- `rubric_based_final_response_quality_v1` - Custom rubric evaluation
- `rubric_based_tool_use_quality_v1` - Tool usage quality
- `hallucinations_v1` - Groundedness checking
- `safety_v1` - Safety/harmlessness checking
