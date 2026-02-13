"""
Pytest-based evaluation tests for the travel agent.

Run: uv run pytest test_travel_agent.py -v
"""

import json
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
load_dotenv()

from google.adk.evaluation.agent_evaluator import AgentEvaluator


def _write_config(criteria: dict):
    """Write test_config.json (auto-discovered by AgentEvaluator)."""
    config = {"criteria": criteria}
    Path("tests/test_config.json").write_text(json.dumps(config, indent=2))


@pytest.mark.asyncio
async def test_basic_functionality():
    """Test basic search and booking functionality."""
    os.chdir(Path(__file__).parent)
    _write_config({"tool_trajectory_avg_score": 1.0, "response_match_score": 0.5})
    await AgentEvaluator.evaluate(
        agent_module="travel_agent",
        eval_dataset_file_path_or_dir="tests/01_basic.test.json",
        num_runs=1,
        print_detailed_results=True,
    )


@pytest.mark.asyncio
async def test_response_quality():
    """Test response quality with ROUGE-1 matching."""
    os.chdir(Path(__file__).parent)
    _write_config({"response_match_score": 0.3})
    await AgentEvaluator.evaluate(
        agent_module="travel_agent",
        eval_dataset_file_path_or_dir="tests/02_response.test.json",
        num_runs=1,
        print_detailed_results=True,
    )


@pytest.mark.asyncio
async def test_trajectory_matching():
    """Test trajectory with IN_ORDER matching."""
    os.chdir(Path(__file__).parent)
    _write_config({"tool_trajectory_avg_score": {"threshold": 1.0, "match_type": 1}})
    await AgentEvaluator.evaluate(
        agent_module="travel_agent",
        eval_dataset_file_path_or_dir="tests/03_trajectory.test.json",
        num_runs=1,
        print_detailed_results=True,
    )


@pytest.mark.asyncio
async def test_multiturn_conversations():
    """Test multi-turn conversation evaluation."""
    os.chdir(Path(__file__).parent)
    _write_config({"tool_trajectory_avg_score": 1.0, "response_match_score": 0.4})
    await AgentEvaluator.evaluate(
        agent_module="travel_agent",
        eval_dataset_file_path_or_dir="tests/04_multiturn.test.json",
        num_runs=1,
        print_detailed_results=True,
    )


@pytest.mark.asyncio
async def test_rubric_evaluation():
    """Test rubric-based evaluation."""
    os.chdir(Path(__file__).parent)
    _write_config({
        "rubric_based_final_response_quality_v1": {
            "threshold": 0.8,
            "judge_model_options": {"judge_model": "gemini-2.0-flash", "num_samples": 3},
            "rubrics": [
                {"rubric_id": "accuracy", "rubric_content": {"text_property": "The response accurately reflects the data returned by tools."}},
                {"rubric_id": "helpfulness", "rubric_content": {"text_property": "The response is helpful and answers the user's question."}},
            ],
        }
    })
    await AgentEvaluator.evaluate(
        agent_module="travel_agent",
        eval_dataset_file_path_or_dir="tests/05_rubrics.test.json",
        num_runs=1,
        print_detailed_results=True,
    )
