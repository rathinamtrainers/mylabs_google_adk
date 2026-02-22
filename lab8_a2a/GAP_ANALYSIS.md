# Lab 8 A2A Protocol - Gap Analysis

**Date:** 2026-02-14
**Official Documentation:** https://google.github.io/adk-docs/a2a/

## Executive Summary

The current lab8_a2a exercises provide a **solid foundation** for A2A protocol basics but are **missing 15 advanced features** that would make this a comprehensive demonstration. The gaps range from critical production features (authentication, error handling) to advanced capabilities (streaming, custom converters, artifact handling).

---

## Current Coverage ✅

| Exercise | Topic | Status |
|----------|-------|--------|
| 01 | A2A Basics | ✅ Comprehensive |
| 02 | Exposing Agents | ✅ Good coverage of to_a2a() |
| 03 | Consuming Agents | ✅ Good coverage of RemoteA2aAgent |
| 04 | Agent Cards | ✅ Covers structure and AgentCardBuilder |
| 05 | Distributed Agents | ✅ Realistic multi-process demo |

**Strengths:**
- Clear progression from basics to distributed systems
- Good explanatory text and documentation
- Realistic use cases (math, weather, translator agents)
- Both in-process and multi-process demos
- Well-structured code with good comments

---

## Critical Gaps 🔴

### 1. **Authentication & Authorization**
**Severity:** HIGH (Production Requirement)

**Missing:**
- No demonstration of `security_schemes` in AgentCardBuilder
- No authenticated agent card examples
- No custom `a2a_request_meta_provider` for auth tokens
- No middleware for authentication/authorization
- No examples of protected endpoints

**What Should Be Added:**
```python
# Exercise 06: Authentication
# - API key authentication
# - OAuth2 token-based auth
# - Custom metadata provider for request headers
# - Protected agent endpoints
# - Agent card with security_schemes
```

**Use Cases:**
- Enterprise agents requiring API keys
- Multi-tenant systems with user isolation
- Cross-organization agent collaboration with auth

---

### 2. **Custom Session Services**
**Severity:** MEDIUM (Production Requirement)

**Missing:**
- All exercises use `InMemorySessionService` only
- No demonstration of persistent session services
- No custom runner configuration with different services
- No session sharing across distributed agents

**What Should Be Added:**
```python
# Add to Exercise 05 or create new exercise:
# - DatabaseSessionService example
# - Custom session service implementation
# - Session persistence across restarts
# - Passing custom runner to to_a2a()
```

---

### 3. **Artifact Handling & Streaming**
**Severity:** MEDIUM (Advanced Feature)

**Missing:**
- No artifact streaming examples
- No `TaskArtifactUpdateEvent` demonstration
- No partial artifact updates
- No streaming task status updates
- No thought streaming

**What Should Be Added:**
```python
# Exercise 06: Streaming & Artifacts
# - Agent that generates artifacts (images, files)
# - Streaming status updates (submitted → working → completed)
# - Partial artifact updates with append/last_chunk
# - Thought streaming for reasoning visibility
```

**Real-World Use Cases:**
- Image generation agent with progress updates
- Long-running data processing with status
- Document generation with streaming chunks

---

### 4. **Advanced Error Handling**
**Severity:** HIGH (Production Requirement)

**Missing:**
- No timeout configuration examples
- No connection failure recovery
- No retry logic demonstration
- No circuit breaker patterns
- No graceful degradation
- No task state management (failed, auth_required, input_required)

**What Should Be Added:**
```python
# Add to Exercise 03 or create new:
# - Timeout handling with custom timeout values
# - Connection error recovery
# - Fallback to local agent when remote fails
# - Task state transitions demonstration
# - AgentCardResolutionError handling
```

---

### 5. **Production Deployment Features**
**Severity:** HIGH (Production Requirement)

**Missing:**
- No HTTPS configuration
- No CORS middleware examples
- No rate limiting
- No load balancing demonstrations
- No health check endpoints
- No monitoring/observability setup

**What Should Be Added:**
```python
# Exercise 07: Production Deployment
# - HTTPS with SSL certificates
# - CORS configuration for web clients
# - Rate limiting middleware
# - Health check endpoints
# - Prometheus metrics integration
# - Docker/Kubernetes deployment examples
```

---

## Moderate Gaps 🟡

### 6. **Request Metadata Provider**
**Missing:** Custom `a2a_request_meta_provider` examples

**Impact:** Limits ability to add tracing, feature flags, user context

**Suggested Addition:**
```python
# Exercise 06 addition:
def custom_metadata_provider(ctx: InvocationContext, msg: A2AMessage) -> dict:
    return {
        "trace_id": ctx.invocation_id,
        "user_tier": ctx.state.get("user:tier", "free"),
        "feature_flags": ["streaming", "artifacts"]
    }

remote_agent = RemoteA2aAgent(
    name="tracked_agent",
    agent_card="...",
    a2a_request_meta_provider=custom_metadata_provider
)
```

---

### 7. **Custom Part Converters**
**Missing:** Examples of custom `genai_part_converter` and `a2a_part_converter`

**Impact:** Cannot handle custom data formats or proprietary encodings

**Suggested Addition:**
```python
# Exercise: Custom Data Formats
def custom_genai_to_a2a(part: Part) -> DataPart:
    # Custom conversion logic for special data types
    pass

remote_agent = RemoteA2aAgent(
    name="custom_format_agent",
    genai_part_converter=custom_genai_to_a2a,
    a2a_part_converter=custom_a2a_to_genai
)
```

---

### 8. **Alternative Exposure Method**
**Missing:** Manual agent card + `adk api_server --a2a` method

**Impact:** Users unaware of multiple-agents-per-server deployment option

**Suggested Addition:**
```python
# Exercise 08: Multi-Agent Server
# Directory structure:
# multi_agent_server/
#   agent1/
#     __init__.py (exports root_agent)
#     agent-card.json
#   agent2/
#     __init__.py
#     agent-card.json
#
# Run: adk api_server --a2a --port 8000 multi_agent_server/
```

---

### 9. **Agent Card Advanced Features**
**Missing:**
- `doc_url` for documentation links
- `provider` metadata (name, url, support_email)
- `capabilities` object usage
- `supports_authenticated_extended_card` flag
- Custom skill tags beyond basics

**Suggested Addition:**
```python
# Add to Exercise 04:
from google.adk.a2a.utils.agent_card_builder import (
    AgentCardBuilder, AgentCapabilities, AgentProvider
)

builder = AgentCardBuilder(
    agent=agent,
    rpc_url="http://localhost:8001",
    doc_url="https://docs.example.com/agent",
    provider=AgentProvider(
        name="Example Corp",
        url="https://example.com",
        support_email="support@example.com"
    ),
    agent_version="2.1.0",
    capabilities=AgentCapabilities(streaming=True, artifacts=True)
)
```

---

### 10. **Logging & Debugging**
**Missing:**
- No structured logging examples
- No `build_a2a_request_log()` / `build_a2a_response_log()` usage
- No debug mode configuration
- No request/response tracing

**Suggested Addition:**
```python
# Exercise: Debugging A2A Communication
import logging
from google.adk.a2a.logs.log_utils import build_a2a_request_log

# Start server with debug logging
adk api_server --a2a --log_level debug --port 8001

# Client-side logging setup
logging.basicConfig(level=logging.DEBUG)
```

---

## Minor Gaps 🟢

### 11. **HTTP Client Configuration**
**Missing:** Custom `httpx.AsyncClient` configuration, `A2AClientFactory`

### 12. **Agent Card Resolution from File**
**Missing:** Examples loading agent cards from local JSON files

### 13. **Stateless Interactions**
**Missing:** A2A v0.2 stateless interaction mode demonstration

### 14. **Multi-Modal Agents**
**Missing:** Agents with image/audio input/output modes demonstration

### 15. **Well-Known Path Customization**
**Missing:** Custom agent card endpoint paths (though standard is fine)

---

## Recommended Additions

### Option A: Expand Existing Exercises (Conservative)
1. **Exercise 03** - Add error handling section
2. **Exercise 04** - Add provider metadata and doc_url
3. **Exercise 05** - Add custom session service option
4. **New Exercise 06** - Authentication & Security
5. **New Exercise 07** - Streaming & Artifacts
6. **New Exercise 08** - Production Deployment

### Option B: Complete Rewrite (Comprehensive)
Restructure into 10 exercises covering all features:
1. Basics (current 01)
2. Exposing Agents (current 02)
3. Consuming Agents (current 03)
4. Agent Cards (current 04)
5. Error Handling & Timeouts
6. Authentication & Security
7. Streaming & Artifacts
8. Custom Services & Converters
9. Production Deployment
10. Distributed System (current 05)

### Option C: Additional Labs (Modular)
Keep existing lab8_a2a as "fundamentals", create:
- **lab8b_a2a_advanced** - Auth, streaming, artifacts, custom services
- **lab8c_a2a_production** - HTTPS, monitoring, deployment, scale

---

## Priority Matrix

| Feature | Importance | Complexity | Priority |
|---------|-----------|------------|----------|
| Authentication | HIGH | MEDIUM | 🔴 P0 |
| Error Handling | HIGH | LOW | 🔴 P0 |
| Production Setup | HIGH | MEDIUM | 🔴 P0 |
| Streaming | MEDIUM | MEDIUM | 🟡 P1 |
| Artifacts | MEDIUM | MEDIUM | 🟡 P1 |
| Custom Services | MEDIUM | LOW | 🟡 P1 |
| Logging/Debug | MEDIUM | LOW | 🟡 P1 |
| Request Metadata | LOW | LOW | 🟢 P2 |
| Custom Converters | LOW | MEDIUM | 🟢 P2 |
| Multi-Agent Server | LOW | LOW | 🟢 P2 |

---

## Conclusion

The current lab8_a2a exercises provide **excellent foundational coverage** (70% of core features) but are **missing critical production features** needed for real-world deployment.

**Recommendation:** Pursue **Option A** (expand existing exercises) as it balances completeness with maintainability, adding 3 new exercises to cover the P0 and P1 gaps.

**Estimated Effort:**
- P0 additions: 8-10 hours
- P1 additions: 6-8 hours
- P2 additions: 4-6 hours
- **Total:** 18-24 hours for comprehensive coverage

---

## Sources

- [ADK with Agent2Agent (A2A) Protocol](https://google.github.io/adk-docs/a2a/)
- [Introduction to A2A](https://google.github.io/adk-docs/a2a/intro/)
- [Quickstart: Exposing a remote agent via A2A](https://google.github.io/adk-docs/a2a/quickstart-exposing/)
- [Quickstart: Consuming a remote agent via A2A](https://google.github.io/adk-docs/a2a/quickstart-consuming/)
- [What's new with Agents: ADK, Agent Engine, and A2A Enhancements](https://developers.googleblog.com/en/agents-adk-agent-engine-a2a-enhancements-google-io/)
- [Unlock AI agent collaboration: Convert ADK agents for A2A](https://cloud.google.com/blog/products/ai-machine-learning/unlock-ai-agent-collaboration-convert-adk-agents-for-a2a)
