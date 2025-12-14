"""
Lab 3 - Exercise 4: Callback Design Patterns
=============================================

This exercise demonstrates common callback patterns:
1. Content guardrails (input/output filtering)
2. Request logging and metrics
3. Rate limiting
4. Response sanitization
5. Combining multiple callbacks

Run: uv run python 04_callback_patterns.py
"""

import asyncio
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools import FunctionTool, BaseTool, ToolContext
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# =============================================================================
# Pattern 1: Content Guardrails
# =============================================================================

@dataclass
class GuardrailConfig:
    """Configuration for content guardrails."""
    blocked_input_words: List[str] = field(default_factory=lambda: [
        "hack", "exploit", "bypass", "crack", "illegal"
    ])
    blocked_output_patterns: List[str] = field(default_factory=lambda: [
        "password", "credit card", "ssn", "social security"
    ])
    max_input_length: int = 1000
    max_output_length: int = 2000


def create_guardrail_callbacks(config: GuardrailConfig):
    """Factory function to create guardrail callbacks."""

    def input_guardrail(
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """Check input against guardrail rules."""
        if not llm_request.contents:
            return None

        last_content = llm_request.contents[-1]
        if not last_content.parts:
            return None

        text = getattr(last_content.parts[0], 'text', '') or ''

        # Check length
        if len(text) > config.max_input_length:
            print(f"    [GUARDRAIL] Input too long: {len(text)} > {config.max_input_length}")
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text="Your message is too long. Please shorten it.")]
                )
            )

        # Check blocked words
        text_lower = text.lower()
        for word in config.blocked_input_words:
            if word in text_lower:
                print(f"    [GUARDRAIL] Blocked word: '{word}'")
                return LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part(text="I cannot process this request.")]
                    )
                )

        print("    [GUARDRAIL] Input passed")
        return None

    def output_guardrail(
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> Optional[LlmResponse]:
        """Check output against guardrail rules."""
        if not llm_response.content or not llm_response.content.parts:
            return None

        text = getattr(llm_response.content.parts[0], 'text', '') or ''

        # Check length
        if len(text) > config.max_output_length:
            truncated = text[:config.max_output_length] + "... [truncated]"
            print(f"    [GUARDRAIL] Output truncated: {len(text)} > {config.max_output_length}")
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=truncated)]
                )
            )

        # Check blocked patterns
        text_lower = text.lower()
        for pattern in config.blocked_output_patterns:
            if pattern in text_lower:
                print(f"    [GUARDRAIL] Blocked pattern in output: '{pattern}'")
                return LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part(
                            text="I've filtered my response to remove sensitive information."
                        )]
                    )
                )

        print("    [GUARDRAIL] Output passed")
        return None

    return input_guardrail, output_guardrail


# =============================================================================
# Pattern 2: Logging and Metrics
# =============================================================================

@dataclass
class MetricsCollector:
    """Collects metrics about agent/model/tool usage."""
    requests: int = 0
    responses: int = 0
    tool_calls: int = 0
    total_input_tokens: int = 0  # Estimated
    total_output_tokens: int = 0  # Estimated
    errors: int = 0
    request_times: List[float] = field(default_factory=list)

    def log_request(self, text: str):
        self.requests += 1
        self.total_input_tokens += len(text.split())  # Rough estimate

    def log_response(self, text: str, duration: float):
        self.responses += 1
        self.total_output_tokens += len(text.split())
        self.request_times.append(duration)

    def log_tool_call(self):
        self.tool_calls += 1

    def summary(self) -> dict:
        avg_time = sum(self.request_times) / len(self.request_times) if self.request_times else 0
        return {
            "requests": self.requests,
            "responses": self.responses,
            "tool_calls": self.tool_calls,
            "est_input_tokens": self.total_input_tokens,
            "est_output_tokens": self.total_output_tokens,
            "avg_response_time": round(avg_time, 3),
        }


def create_metrics_callbacks(metrics: MetricsCollector):
    """Factory function to create metrics tracking callbacks."""

    request_start_time = {}

    def before_model(
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """Log request metrics."""
        request_start_time[callback_context.invocation_id] = time.time()

        if llm_request.contents:
            text = getattr(llm_request.contents[-1].parts[0], 'text', '') or ''
            metrics.log_request(text)
            print(f"    [METRICS] Request #{metrics.requests}")

        return None

    def after_model(
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> Optional[LlmResponse]:
        """Log response metrics."""
        duration = time.time() - request_start_time.get(callback_context.invocation_id, time.time())

        if llm_response.content and llm_response.content.parts:
            text = getattr(llm_response.content.parts[0], 'text', '') or ''
            metrics.log_response(text, duration)
            print(f"    [METRICS] Response in {duration:.3f}s")

        return None

    def after_tool(
        tool: BaseTool,
        args: Dict[str, Any],
        tool_context: ToolContext,
        tool_response: Dict
    ) -> Optional[Dict]:
        """Log tool usage."""
        metrics.log_tool_call()
        print(f"    [METRICS] Tool call: {tool.name}")
        return None

    return before_model, after_model, after_tool


# =============================================================================
# Pattern 3: Rate Limiting
# =============================================================================

@dataclass
class RateLimiter:
    """Simple rate limiter."""
    max_requests_per_minute: int = 10
    request_timestamps: List[float] = field(default_factory=list)

    def check_rate(self) -> bool:
        """Returns True if request is allowed."""
        now = time.time()
        # Remove timestamps older than 1 minute
        self.request_timestamps = [
            ts for ts in self.request_timestamps
            if now - ts < 60
        ]
        return len(self.request_timestamps) < self.max_requests_per_minute

    def record_request(self):
        """Record a new request."""
        self.request_timestamps.append(time.time())


def create_rate_limit_callback(limiter: RateLimiter):
    """Factory function to create rate limiting callback."""

    def rate_limit_check(
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """Check rate limit before processing."""
        if not limiter.check_rate():
            remaining = 60 - (time.time() - limiter.request_timestamps[0])
            print(f"    [RATE LIMIT] Exceeded! Wait {remaining:.0f}s")
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(
                        text=f"Rate limit exceeded. Please wait {remaining:.0f} seconds."
                    )]
                )
            )

        limiter.record_request()
        print(f"    [RATE LIMIT] {len(limiter.request_timestamps)}/{limiter.max_requests_per_minute} requests")
        return None

    return rate_limit_check


# =============================================================================
# Pattern 4: Response Sanitization
# =============================================================================

def create_sanitization_callback(patterns_to_redact: List[str]):
    """Factory function to create sanitization callback."""

    def sanitize_response(
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> Optional[LlmResponse]:
        """Redact sensitive patterns from response."""
        if not llm_response.content or not llm_response.content.parts:
            return None

        text = getattr(llm_response.content.parts[0], 'text', '') or ''
        modified = False

        for pattern in patterns_to_redact:
            if pattern.lower() in text.lower():
                # Case-insensitive replacement
                import re
                text = re.sub(
                    re.escape(pattern),
                    "[REDACTED]",
                    text,
                    flags=re.IGNORECASE
                )
                modified = True
                print(f"    [SANITIZE] Redacted: '{pattern}'")

        if modified:
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=text)]
                )
            )

        return None

    return sanitize_response


# =============================================================================
# Pattern 5: Callback Chaining (Multiple Callbacks)
# =============================================================================

def chain_before_model_callbacks(*callbacks):
    """Chain multiple before_model callbacks together."""

    def chained_callback(
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        for cb in callbacks:
            result = cb(callback_context, llm_request)
            if result is not None:
                # If any callback returns a response, stop the chain
                return result
        return None

    return chained_callback


def chain_after_model_callbacks(*callbacks):
    """Chain multiple after_model callbacks together."""

    def chained_callback(
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> Optional[LlmResponse]:
        current_response = llm_response
        for cb in callbacks:
            result = cb(callback_context, current_response)
            if result is not None:
                current_response = result
        # Return final modified response, or None if no modifications
        return current_response if current_response != llm_response else None

    return chained_callback


# =============================================================================
# Sample Tool for Testing
# =============================================================================

def get_user_data(user_id: str) -> dict:
    """Get mock user data."""
    return {
        "user_id": user_id,
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "555-123-4567"
    }

user_data_tool = FunctionTool(func=get_user_data)


async def main():
    print("\n" + "#"*70)
    print("# Lab 3 Exercise 4: Callback Design Patterns")
    print("#"*70)

    session_service = InMemorySessionService()

    # =========================================================================
    # Pattern 1: Content Guardrails
    # =========================================================================
    print("\n" + "="*60)
    print("PATTERN 1: Content Guardrails")
    print("="*60)

    config = GuardrailConfig(
        blocked_input_words=["hack", "exploit"],
        blocked_output_patterns=["password", "secret"],
        max_input_length=500
    )
    input_guard, output_guard = create_guardrail_callbacks(config)

    agent1 = LlmAgent(
        name="GuardedAgent",
        model="gemini-2.0-flash",
        instruction="You are helpful. Keep responses brief.",
        before_model_callback=input_guard,
        after_model_callback=output_guard,
    )

    runner1 = Runner(
        agent=agent1,
        app_name="patterns_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="patterns_demo",
        user_id="user1",
        session_id="guardrail_session",
        state={}
    )

    # Test blocked input
    print("\n  Test: Blocked input word")
    user_message = types.Content(parts=[types.Part(text="How do I hack a system?")])
    async for event in runner1.run_async(
        user_id="user1",
        session_id="guardrail_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text}")

    # Test safe input
    print("\n  Test: Safe input")
    user_message = types.Content(parts=[types.Part(text="What is Python?")])
    async for event in runner1.run_async(
        user_id="user1",
        session_id="guardrail_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text[:80]}...")

    # =========================================================================
    # Pattern 2: Logging and Metrics
    # =========================================================================
    print("\n" + "="*60)
    print("PATTERN 2: Logging and Metrics")
    print("="*60)

    metrics = MetricsCollector()
    before_model, after_model, after_tool = create_metrics_callbacks(metrics)

    agent2 = LlmAgent(
        name="MetricsAgent",
        model="gemini-2.0-flash",
        instruction="You help with user data. Use tools when needed.",
        tools=[user_data_tool],
        before_model_callback=before_model,
        after_model_callback=after_model,
        after_tool_callback=after_tool,
    )

    runner2 = Runner(
        agent=agent2,
        app_name="patterns_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="patterns_demo",
        user_id="user1",
        session_id="metrics_session",
        state={}
    )

    print("\n  Making 3 requests...")
    questions = [
        "What is 2+2?",
        "Get user data for user123",
        "What is the capital of France?",
    ]

    for q in questions:
        print(f"\n  Q: {q}")
        user_message = types.Content(parts=[types.Part(text=q)])
        async for event in runner2.run_async(
            user_id="user1",
            session_id="metrics_session",
            new_message=user_message,
        ):
            if event.is_final_response() and event.content:
                pass  # Just process

    print(f"\n  Metrics Summary: {metrics.summary()}")

    # =========================================================================
    # Pattern 3: Rate Limiting
    # =========================================================================
    print("\n" + "="*60)
    print("PATTERN 3: Rate Limiting")
    print("="*60)

    limiter = RateLimiter(max_requests_per_minute=3)  # Low limit for demo
    rate_check = create_rate_limit_callback(limiter)

    agent3 = LlmAgent(
        name="RateLimitedAgent",
        model="gemini-2.0-flash",
        instruction="You are helpful. Keep responses under 10 words.",
        before_model_callback=rate_check,
    )

    runner3 = Runner(
        agent=agent3,
        app_name="patterns_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="patterns_demo",
        user_id="user1",
        session_id="ratelimit_session",
        state={}
    )

    print("\n  Sending 5 requests (limit is 3/minute)...")
    for i in range(5):
        print(f"\n  Request {i+1}:")
        user_message = types.Content(parts=[types.Part(text=f"Count to {i+1}")])
        async for event in runner3.run_async(
            user_id="user1",
            session_id="ratelimit_session",
            new_message=user_message,
        ):
            if event.is_final_response() and event.content:
                print(f"  Response: {event.content.parts[0].text[:60]}...")

    # =========================================================================
    # Pattern 4: Response Sanitization
    # =========================================================================
    print("\n" + "="*60)
    print("PATTERN 4: Response Sanitization")
    print("="*60)

    sanitize = create_sanitization_callback(["example.com", "555-123"])

    agent4 = LlmAgent(
        name="SanitizedAgent",
        model="gemini-2.0-flash",
        instruction="You help with user data. Mention example.com and phone numbers.",
        tools=[user_data_tool],
        after_model_callback=sanitize,
    )

    runner4 = Runner(
        agent=agent4,
        app_name="patterns_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="patterns_demo",
        user_id="user1",
        session_id="sanitize_session",
        state={}
    )

    print("\n  Getting user data (with sanitization)...")
    user_message = types.Content(parts=[types.Part(text="Get user data for user123")])
    async for event in runner4.run_async(
        user_id="user1",
        session_id="sanitize_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text[:150]}...")

    # =========================================================================
    # Pattern 5: Callback Chaining
    # =========================================================================
    print("\n" + "="*60)
    print("PATTERN 5: Callback Chaining")
    print("="*60)

    # Create individual callbacks
    guard_config = GuardrailConfig(blocked_input_words=["forbidden"])
    guard_input, guard_output = create_guardrail_callbacks(guard_config)

    metrics2 = MetricsCollector()
    metrics_before, metrics_after, _ = create_metrics_callbacks(metrics2)

    # Chain them together
    chained_before = chain_before_model_callbacks(guard_input, metrics_before)
    chained_after = chain_after_model_callbacks(guard_output, metrics_after)

    agent5 = LlmAgent(
        name="ChainedAgent",
        model="gemini-2.0-flash",
        instruction="You are helpful. Keep responses brief.",
        before_model_callback=chained_before,
        after_model_callback=chained_after,
    )

    runner5 = Runner(
        agent=agent5,
        app_name="patterns_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="patterns_demo",
        user_id="user1",
        session_id="chained_session",
        state={}
    )

    print("\n  Test with chained callbacks (guardrails + metrics)...")
    user_message = types.Content(parts=[types.Part(text="What is AI?")])
    async for event in runner5.run_async(
        user_id="user1",
        session_id="chained_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text[:80]}...")

    print(f"\n  Chained metrics: {metrics2.summary()}")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Callback Design Patterns")
    print("#"*70)
    print("""
    PATTERN 1: CONTENT GUARDRAILS
    -----------------------------
    - Check input for blocked words/patterns
    - Filter output for sensitive information
    - Enforce length limits
    - Use factory functions for configurability

    PATTERN 2: LOGGING AND METRICS
    ------------------------------
    - Track request/response counts
    - Measure response times
    - Count tool usage
    - Estimate token usage
    - Use dataclass to collect metrics

    PATTERN 3: RATE LIMITING
    ------------------------
    - Limit requests per time window
    - Track timestamps of requests
    - Return friendly error when exceeded
    - Clear old timestamps to reset window

    PATTERN 4: RESPONSE SANITIZATION
    --------------------------------
    - Redact sensitive patterns
    - Remove PII (emails, phones, etc.)
    - Case-insensitive matching
    - Replace with [REDACTED] placeholder

    PATTERN 5: CALLBACK CHAINING
    ----------------------------
    - Combine multiple callbacks
    - before_model: First to return wins
    - after_model: Chain modifications
    - Modular and reusable design

    FACTORY PATTERN:
    ----------------
    def create_callback(config):
        def callback(context, request):
            # Use config here
            pass
        return callback

    This allows:
    - Configurable callbacks
    - Shared state via closure
    - Reusable across agents

    BEST PRACTICES:
    ---------------
    1. Use factory functions for configuration
    2. Keep callbacks focused (single responsibility)
    3. Chain callbacks for complex logic
    4. Log actions for debugging
    5. Return None to allow normal flow
    6. Test callbacks independently
    """)


if __name__ == "__main__":
    asyncio.run(main())
