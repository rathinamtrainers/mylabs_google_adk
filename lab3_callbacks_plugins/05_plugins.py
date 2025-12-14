"""
Lab 3 - Exercise 5: Plugins
============================

This exercise demonstrates creating plugins with BasePlugin:
1. Understanding BasePlugin class
2. Plugin lifecycle callbacks
3. Global vs agent-level callbacks
4. Building practical plugins

Run: uv run python 05_plugins.py
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
from google.adk.plugins.base_plugin import BasePlugin
from google.genai import types


# =============================================================================
# Part 1: Basic Plugin Structure
# =============================================================================

class SimpleLoggingPlugin(BasePlugin):
    """
    A simple plugin that logs all agent and model interactions.

    Plugins extend BasePlugin and override callback methods.
    They apply GLOBALLY to all agents in the runner.
    """

    def __init__(self):
        # name is required - identifies the plugin
        super().__init__(name="simple_logging")
        self.log_entries: List[str] = []

    async def before_agent_callback(
        self,
        *,
        agent,  # The agent being executed
        callback_context: CallbackContext
    ) -> Optional[types.Content]:
        """Called before any agent runs."""
        entry = f"[AGENT START] {agent.name}"
        self.log_entries.append(entry)
        print(f"    {entry}")
        return None  # Allow agent to proceed

    async def after_agent_callback(
        self,
        *,
        agent,
        callback_context: CallbackContext
    ) -> Optional[types.Content]:
        """Called after any agent completes."""
        entry = f"[AGENT END] {agent.name}"
        self.log_entries.append(entry)
        print(f"    {entry}")
        return None

    async def before_model_callback(
        self,
        *,
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """Called before any LLM request."""
        entry = f"[MODEL REQUEST] {llm_request.model}"
        self.log_entries.append(entry)
        print(f"    {entry}")
        return None

    async def after_model_callback(
        self,
        *,
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> Optional[LlmResponse]:
        """Called after any LLM response."""
        entry = "[MODEL RESPONSE] received"
        self.log_entries.append(entry)
        print(f"    {entry}")
        return None

    def get_logs(self) -> List[str]:
        """Get all log entries."""
        return self.log_entries.copy()


# =============================================================================
# Part 2: Metrics Plugin
# =============================================================================

@dataclass
class PluginMetrics:
    """Metrics collected by the plugin."""
    agent_calls: int = 0
    model_calls: int = 0
    tool_calls: int = 0
    total_latency: float = 0.0
    errors: int = 0


class MetricsPlugin(BasePlugin):
    """
    Plugin that collects detailed metrics about agent execution.
    """

    def __init__(self):
        super().__init__(name="metrics")
        self.metrics = PluginMetrics()
        self._start_times: Dict[str, float] = {}

    async def before_agent_callback(
        self,
        *,
        agent,
        callback_context: CallbackContext
    ) -> Optional[types.Content]:
        """Track agent call start."""
        self.metrics.agent_calls += 1
        self._start_times[callback_context.invocation_id] = time.time()
        return None

    async def after_agent_callback(
        self,
        *,
        agent,
        callback_context: CallbackContext
    ) -> Optional[types.Content]:
        """Track agent call end and latency."""
        start = self._start_times.pop(callback_context.invocation_id, time.time())
        latency = time.time() - start
        self.metrics.total_latency += latency
        return None

    async def before_model_callback(
        self,
        *,
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """Track model calls."""
        self.metrics.model_calls += 1
        return None

    async def before_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: Dict[str, Any],
        tool_context: ToolContext
    ) -> Optional[Dict]:
        """Track tool calls."""
        self.metrics.tool_calls += 1
        return None

    def get_metrics(self) -> dict:
        """Get metrics summary."""
        avg_latency = (
            self.metrics.total_latency / self.metrics.agent_calls
            if self.metrics.agent_calls > 0 else 0
        )
        return {
            "agent_calls": self.metrics.agent_calls,
            "model_calls": self.metrics.model_calls,
            "tool_calls": self.metrics.tool_calls,
            "total_latency_sec": round(self.metrics.total_latency, 3),
            "avg_latency_sec": round(avg_latency, 3),
        }


# =============================================================================
# Part 3: Guardrail Plugin
# =============================================================================

class GuardrailPlugin(BasePlugin):
    """
    Plugin that enforces content guardrails across all agents.
    """

    def __init__(self, blocked_words: List[str] = None):
        super().__init__(name="guardrail")
        self.blocked_words = blocked_words or ["hack", "exploit", "illegal"]
        self.blocked_count = 0

    async def before_model_callback(
        self,
        *,
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """Check input for blocked content."""
        if not llm_request.contents:
            return None

        last_content = llm_request.contents[-1]
        if not last_content.parts:
            return None

        text = getattr(last_content.parts[0], 'text', '') or ''
        text_lower = text.lower()

        for word in self.blocked_words:
            if word in text_lower:
                self.blocked_count += 1
                print(f"    [GUARDRAIL PLUGIN] Blocked: '{word}'")
                return LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part(
                            text="I cannot process requests with prohibited content."
                        )]
                    )
                )

        return None

    def get_stats(self) -> dict:
        """Get guardrail statistics."""
        return {
            "blocked_words": self.blocked_words,
            "blocked_count": self.blocked_count,
        }


# =============================================================================
# Part 4: Context Enrichment Plugin
# =============================================================================

class ContextEnrichmentPlugin(BasePlugin):
    """
    Plugin that enriches every request with additional context.
    """

    def __init__(self, context_prefix: str = ""):
        super().__init__(name="context_enrichment")
        self.context_prefix = context_prefix
        self.enrichments_applied = 0

    async def before_model_callback(
        self,
        *,
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """Add context from state to the system instruction."""
        # Get user preferences from state
        user_name = callback_context.state.get("user_name", "User")
        user_role = callback_context.state.get("user_role", "general user")

        # Build context string
        context = f"\n[Context: User is {user_name}, role: {user_role}]"

        if self.context_prefix:
            context = f"\n{self.context_prefix}{context}"

        # Add to system instruction if available
        if llm_request.config and llm_request.config.system_instruction:
            existing = llm_request.config.system_instruction
            # system_instruction can be a string or Content object
            if isinstance(existing, str):
                enhanced = existing + context
                llm_request.config.system_instruction = enhanced
                self.enrichments_applied += 1
                print(f"    [CONTEXT PLUGIN] Added user context")
            elif hasattr(existing, 'parts') and existing.parts:
                original = getattr(existing.parts[0], 'text', '') or ''
                enhanced = original + context
                existing.parts[0] = types.Part(text=enhanced)
                self.enrichments_applied += 1
                print(f"    [CONTEXT PLUGIN] Added user context")

        return None


# =============================================================================
# Part 5: Audit Plugin
# =============================================================================

@dataclass
class AuditEntry:
    """Single audit log entry."""
    timestamp: float
    event_type: str
    agent_name: str
    details: str


class AuditPlugin(BasePlugin):
    """
    Plugin that creates an audit trail of all operations.
    """

    def __init__(self):
        super().__init__(name="audit")
        self.audit_log: List[AuditEntry] = []

    def _log(self, event_type: str, agent_name: str, details: str):
        """Add entry to audit log."""
        entry = AuditEntry(
            timestamp=time.time(),
            event_type=event_type,
            agent_name=agent_name,
            details=details
        )
        self.audit_log.append(entry)

    async def before_agent_callback(
        self,
        *,
        agent,
        callback_context: CallbackContext
    ) -> Optional[types.Content]:
        self._log("AGENT_START", agent.name, f"user={callback_context.user_id}")
        return None

    async def after_agent_callback(
        self,
        *,
        agent,
        callback_context: CallbackContext
    ) -> Optional[types.Content]:
        self._log("AGENT_END", agent.name, "completed")
        return None

    async def before_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: Dict[str, Any],
        tool_context: ToolContext
    ) -> Optional[Dict]:
        self._log("TOOL_CALL", tool_context.agent_name, f"tool={tool.name}, args={tool_args}")
        return None

    def get_audit_log(self) -> List[dict]:
        """Get formatted audit log."""
        return [
            {
                "time": entry.timestamp,
                "type": entry.event_type,
                "agent": entry.agent_name,
                "details": entry.details
            }
            for entry in self.audit_log
        ]


# =============================================================================
# Sample Tools
# =============================================================================

def get_time() -> dict:
    """Get current time."""
    from datetime import datetime
    return {"time": datetime.now().strftime("%H:%M:%S")}


def add_numbers(a: int, b: int) -> dict:
    """Add two numbers."""
    return {"result": a + b}


time_tool = FunctionTool(func=get_time)
add_tool = FunctionTool(func=add_numbers)


async def main():
    print("\n" + "#"*70)
    print("# Lab 3 Exercise 5: Plugins")
    print("#"*70)

    session_service = InMemorySessionService()

    # =========================================================================
    # Part 1: Basic Plugin
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: Basic Logging Plugin")
    print("="*60)

    logging_plugin = SimpleLoggingPlugin()

    agent1 = LlmAgent(
        name="BasicAgent",
        model="gemini-2.0-flash",
        instruction="You are helpful. Keep responses under 20 words.",
    )

    runner1 = Runner(
        agent=agent1,
        app_name="plugin_demo",
        session_service=session_service,
        plugins=[logging_plugin],  # Attach plugin to runner
    )

    await session_service.create_session(
        app_name="plugin_demo",
        user_id="user1",
        session_id="logging_session",
        state={}
    )

    print("\n  Sending message with logging plugin active...")
    user_message = types.Content(parts=[types.Part(text="What is 2+2?")])
    async for event in runner1.run_async(
        user_id="user1",
        session_id="logging_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"\n  Response: {event.content.parts[0].text}")

    print(f"\n  Plugin log entries: {len(logging_plugin.get_logs())}")
    for entry in logging_plugin.get_logs():
        print(f"    - {entry}")

    # =========================================================================
    # Part 2: Metrics Plugin
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: Metrics Plugin")
    print("="*60)

    metrics_plugin = MetricsPlugin()

    agent2 = LlmAgent(
        name="ToolAgent",
        model="gemini-2.0-flash",
        instruction="You help with time and math. Use tools when needed.",
        tools=[time_tool, add_tool],
    )

    runner2 = Runner(
        agent=agent2,
        app_name="plugin_demo",
        session_service=session_service,
        plugins=[metrics_plugin],
    )

    await session_service.create_session(
        app_name="plugin_demo",
        user_id="user1",
        session_id="metrics_session",
        state={}
    )

    print("\n  Making multiple requests to collect metrics...")
    questions = [
        "What time is it?",
        "Add 5 and 7",
        "What's 10 plus 20?",
    ]

    for q in questions:
        user_message = types.Content(parts=[types.Part(text=q)])
        async for event in runner2.run_async(
            user_id="user1",
            session_id="metrics_session",
            new_message=user_message,
        ):
            if event.is_final_response() and event.content:
                print(f"    Q: {q}")
                print(f"    A: {event.content.parts[0].text[:50]}...")

    print(f"\n  Metrics collected:")
    for key, value in metrics_plugin.get_metrics().items():
        print(f"    {key}: {value}")

    # =========================================================================
    # Part 3: Guardrail Plugin
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: Guardrail Plugin")
    print("="*60)

    guardrail_plugin = GuardrailPlugin(blocked_words=["forbidden", "banned"])

    agent3 = LlmAgent(
        name="GuardedAgent",
        model="gemini-2.0-flash",
        instruction="You are helpful.",
    )

    runner3 = Runner(
        agent=agent3,
        app_name="plugin_demo",
        session_service=session_service,
        plugins=[guardrail_plugin],
    )

    await session_service.create_session(
        app_name="plugin_demo",
        user_id="user1",
        session_id="guardrail_session",
        state={}
    )

    # Test blocked content
    print("\n  Test 1: Message with 'forbidden' word")
    user_message = types.Content(
        parts=[types.Part(text="Tell me about forbidden topics")]
    )
    async for event in runner3.run_async(
        user_id="user1",
        session_id="guardrail_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text}")

    # Test safe content
    print("\n  Test 2: Safe message")
    user_message = types.Content(parts=[types.Part(text="Tell me about Python")])
    async for event in runner3.run_async(
        user_id="user1",
        session_id="guardrail_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text[:60]}...")

    print(f"\n  Guardrail stats: {guardrail_plugin.get_stats()}")

    # =========================================================================
    # Part 4: Multiple Plugins Together
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Multiple Plugins Together")
    print("="*60)

    # Create fresh plugins
    multi_metrics = MetricsPlugin()
    multi_audit = AuditPlugin()
    multi_context = ContextEnrichmentPlugin(context_prefix="[ENHANCED]")

    agent4 = LlmAgent(
        name="MultiPluginAgent",
        model="gemini-2.0-flash",
        instruction="You are a helpful assistant. Address the user by name.",
        tools=[time_tool],
    )

    runner4 = Runner(
        agent=agent4,
        app_name="plugin_demo",
        session_service=session_service,
        plugins=[multi_metrics, multi_audit, multi_context],  # Multiple plugins
    )

    await session_service.create_session(
        app_name="plugin_demo",
        user_id="user1",
        session_id="multi_plugin_session",
        state={
            "user_name": "Alice",
            "user_role": "developer"
        }
    )

    print("\n  User: Alice (developer)")
    print("  Plugins: metrics, audit, context_enrichment")

    user_message = types.Content(parts=[types.Part(text="What time is it?")])
    async for event in runner4.run_async(
        user_id="user1",
        session_id="multi_plugin_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"\n  Response: {event.content.parts[0].text}")

    print(f"\n  Metrics: {multi_metrics.get_metrics()}")
    print(f"\n  Audit log ({len(multi_audit.get_audit_log())} entries):")
    for entry in multi_audit.get_audit_log()[:5]:
        print(f"    [{entry['type']}] {entry['agent']}: {entry['details']}")

    # =========================================================================
    # Part 5: Plugin vs Agent Callbacks
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: Plugin vs Agent-Level Callbacks")
    print("="*60)

    execution_order = []

    # Plugin callback
    class OrderTrackingPlugin(BasePlugin):
        def __init__(self):
            super().__init__(name="order_tracking")

        async def before_model_callback(
            self,
            *,
            callback_context: CallbackContext,
            llm_request: LlmRequest
        ) -> Optional[LlmResponse]:
            execution_order.append("PLUGIN before_model")
            print("    [ORDER] PLUGIN before_model")
            return None

        async def after_model_callback(
            self,
            *,
            callback_context: CallbackContext,
            llm_response: LlmResponse
        ) -> Optional[LlmResponse]:
            execution_order.append("PLUGIN after_model")
            print("    [ORDER] PLUGIN after_model")
            return None

    # Agent-level callback
    def agent_before_model(callback_context, llm_request):
        execution_order.append("AGENT before_model")
        print("    [ORDER] AGENT before_model")
        return None

    def agent_after_model(callback_context, llm_response):
        execution_order.append("AGENT after_model")
        print("    [ORDER] AGENT after_model")
        return None

    order_plugin = OrderTrackingPlugin()

    agent5 = LlmAgent(
        name="OrderAgent",
        model="gemini-2.0-flash",
        instruction="You are helpful. Keep responses under 10 words.",
        before_model_callback=agent_before_model,
        after_model_callback=agent_after_model,
    )

    runner5 = Runner(
        agent=agent5,
        app_name="plugin_demo",
        session_service=session_service,
        plugins=[order_plugin],
    )

    await session_service.create_session(
        app_name="plugin_demo",
        user_id="user1",
        session_id="order_session",
        state={}
    )

    print("\n  Testing execution order...")
    user_message = types.Content(parts=[types.Part(text="Hi")])
    async for event in runner5.run_async(
        user_id="user1",
        session_id="order_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            pass

    print(f"\n  Execution order: {' -> '.join(execution_order)}")
    print("  Note: Plugin callbacks execute BEFORE agent callbacks!")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Plugins")
    print("#"*70)
    print("""
    PLUGIN STRUCTURE:
    -----------------
    from google.adk.plugins.base_plugin import BasePlugin

    class MyPlugin(BasePlugin):
        def __init__(self):
            super().__init__(name="my_plugin")

        async def before_agent_callback(self, *, agent, callback_context):
            return None  # or types.Content to skip

        async def after_agent_callback(self, *, agent, callback_context):
            return None  # or types.Content to replace

        async def before_model_callback(self, *, callback_context, llm_request):
            return None  # or LlmResponse to skip

        async def after_model_callback(self, *, callback_context, llm_response):
            return None  # or LlmResponse to replace

        async def before_tool_callback(self, *, tool, tool_args, tool_context):
            return None  # or dict to skip

        async def after_tool_callback(self, *, tool, tool_args, tool_context, result):
            return None  # or dict to replace

    ATTACHING PLUGINS:
    ------------------
    runner = Runner(
        agent=agent,
        session_service=session_service,
        plugins=[plugin1, plugin2, plugin3],
    )

    PLUGIN vs AGENT CALLBACKS:
    --------------------------
    - Plugins are GLOBAL (apply to all agents)
    - Agent callbacks are LOCAL (specific agent)
    - Plugin callbacks run BEFORE agent callbacks
    - Multiple plugins run in order of registration

    COMMON PLUGIN USE CASES:
    ------------------------
    1. Logging & Monitoring
       - Track all requests/responses
       - Collect metrics
       - Create audit trails

    2. Security & Guardrails
       - Input validation
       - Output filtering
       - Rate limiting

    3. Context Enrichment
       - Add user context
       - Inject system prompts
       - Dynamic configuration

    4. Analytics & Debugging
       - Performance tracking
       - Error monitoring
       - Usage statistics

    BEST PRACTICES:
    ---------------
    1. Keep plugins focused (single responsibility)
    2. Use dataclasses for state management
    3. Make plugins configurable via __init__
    4. Provide getter methods for metrics/logs
    5. Document plugin behavior clearly
    6. Test plugins independently
    """)


if __name__ == "__main__":
    asyncio.run(main())
