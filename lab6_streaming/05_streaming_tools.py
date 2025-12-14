"""
Lab 6 - Exercise 5: Streaming Tools
====================================

This exercise covers streaming tools for real-time updates:
1. What are streaming tools?
2. Simple streaming tools (AsyncGenerator)
3. Video streaming tools (input_stream)
4. Stopping streaming tools
5. Automatic tool execution in run_live()

Run: uv run python 05_streaming_tools.py
"""

import asyncio
from typing import AsyncGenerator
from google.adk.agents import LlmAgent, LiveRequestQueue
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.agents.run_config import RunConfig, StreamingMode


# =============================================================================
# Part 1: What are Streaming Tools?
# =============================================================================

def explain_streaming_tools():
    """Explain streaming tools concept."""
    print("""
    STREAMING TOOLS
    ===============

    Streaming tools allow functions to stream intermediate results
    back to the agent. The agent can respond to each update in real-time.

    REGULAR TOOL:
    -------------
    def get_stock_price(symbol: str) -> dict:
        # Called once, returns once
        return {"price": 150.00}

    STREAMING TOOL:
    ---------------
    async def monitor_stock_price(symbol: str) -> AsyncGenerator[str, None]:
        # Streams multiple results over time
        while True:
            price = await get_live_price(symbol)
            yield f"Price: {price}"
            await asyncio.sleep(1)

    HOW IT WORKS:
    -------------
    1. Agent calls streaming tool
    2. Tool yields intermediate results
    3. Each yield sends data back to agent
    4. Agent can respond to each update
    5. Tool continues until done or stopped

    USE CASES:
    ----------
    - Stock price monitoring
    - Sensor data streaming
    - Progress updates for long tasks
    - Live video/audio analysis
    - Real-time notifications

    IMPORTANT:
    ----------
    Streaming tools ONLY work with run_live() (streaming mode).
    They do NOT work with run_async() (non-streaming mode).

    TWO TYPES:
    ----------
    1. Simple Streaming Tool
       - Returns AsyncGenerator
       - Generates data independently

    2. Video Streaming Tool
       - Takes input_stream: LiveRequestQueue
       - Processes video/audio from user
       - Great for real-time video analysis
    """)


# =============================================================================
# Part 2: Simple Streaming Tools
# =============================================================================

def explain_simple_streaming():
    """Explain simple streaming tools."""
    print("""
    SIMPLE STREAMING TOOLS
    ======================

    A streaming tool that generates data independently.

    REQUIREMENTS:
    -------------
    1. Must be async function
    2. Must return AsyncGenerator
    3. Use yield to send updates

    EXAMPLE: Stock Price Monitor
    ----------------------------
    async def monitor_stock_price(
        stock_symbol: str
    ) -> AsyncGenerator[str, None]:
        '''Monitor price for the given stock symbol.'''

        while True:
            # Get current price (simulated)
            price = await get_live_price(stock_symbol)

            # Yield update to agent
            yield f"The price for {stock_symbol} is ${price}"

            # Wait before next check
            await asyncio.sleep(5)

    EXAMPLE: Progress Updates
    -------------------------
    async def process_large_file(
        filename: str
    ) -> AsyncGenerator[str, None]:
        '''Process file and report progress.'''

        total_lines = count_lines(filename)
        processed = 0

        with open(filename) as f:
            for line in f:
                process_line(line)
                processed += 1

                # Report every 10%
                if processed % (total_lines // 10) == 0:
                    progress = (processed / total_lines) * 100
                    yield f"Progress: {progress:.0f}%"

        yield "Processing complete!"

    REGISTERING WITH AGENT:
    -----------------------
    agent = Agent(
        name="monitor_agent",
        model="gemini-2.0-flash",
        tools=[monitor_stock_price],  # Just add it!
        instruction="Monitor things as requested."
    )

    AGENT BEHAVIOR:
    ---------------
    User: "Monitor Apple stock for me"
    Agent: *calls monitor_stock_price("AAPL")*
    Tool: yields "Price: $150"
    Agent: "Apple is currently at $150"
    Tool: yields "Price: $155"
    Agent: "Apple went up to $155!"
    ...continues until stopped...
    """)


# =============================================================================
# Part 3: Video Streaming Tools
# =============================================================================

def explain_video_streaming_tools():
    """Explain video streaming tools with input_stream."""
    print("""
    VIDEO STREAMING TOOLS
    =====================

    Tools that process the user's video/audio stream.

    KEY PARAMETER:
    --------------
    input_stream: LiveRequestQueue

    This is a RESERVED parameter name. ADK automatically injects
    the video/audio stream into this parameter.

    EXAMPLE: People Counter
    -----------------------
    async def monitor_video_stream(
        input_stream: LiveRequestQueue,  # ADK injects this!
    ) -> AsyncGenerator[str, None]:
        '''Count people in video stream.'''

        last_count = None

        while True:
            # Get latest frame from stream
            live_req = await input_stream.get()

            if live_req.blob and live_req.blob.mime_type == "image/jpeg":
                # Analyze the frame
                count = await count_people(live_req.blob.data)

                # Only report changes
                if count != last_count:
                    last_count = count
                    yield f"People count changed to: {count}"

            await asyncio.sleep(0.5)

    HOW IT WORKS:
    -------------
    1. User streams video via queue.send_realtime()
    2. ADK routes video to your tool's input_stream
    3. Tool processes frames and yields updates
    4. Agent receives updates and responds

    FULL EXAMPLE:
    -------------
    async def monitor_video_stream(
        input_stream: LiveRequestQueue,
    ) -> AsyncGenerator[str, None]:
        '''Monitor video for changes.'''

        # Use another model for image analysis
        client = Client(vertexai=False)
        prompt = "Count the people in this image. Respond with just a number."
        last_count = None

        while True:
            # Drain queue to get latest frame
            last_frame = None
            while input_stream._queue.qsize() > 0:
                req = await input_stream.get()
                if req.blob and req.blob.mime_type == "image/jpeg":
                    last_frame = req

            if last_frame:
                # Analyze with vision model
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[
                        types.Part.from_bytes(
                            data=last_frame.blob.data,
                            mime_type="image/jpeg"
                        ),
                        types.Part.from_text(prompt)
                    ]
                )

                count = response.text
                if count != last_count:
                    last_count = count
                    yield f"People count: {count}"

            await asyncio.sleep(0.5)

    USE CASES:
    ----------
    - Security monitoring
    - Traffic analysis
    - Quality inspection
    - Activity recognition
    - Object tracking
    """)


# =============================================================================
# Part 4: Stopping Streaming Tools
# =============================================================================

def explain_stopping():
    """Explain how to stop streaming tools."""
    print("""
    STOPPING STREAMING TOOLS
    ========================

    Streaming tools run indefinitely. You need a way to stop them.

    PATTERN: stop_streaming FUNCTION
    ---------------------------------
    Define a function that the agent can call to stop a streaming tool.

    def stop_streaming(function_name: str):
        '''Stop a streaming tool.

        Args:
            function_name: Name of the streaming function to stop.
        '''
        pass  # ADK handles the actual stopping

    Register with agent:
    agent = Agent(
        name="monitor_agent",
        tools=[
            monitor_stock_price,
            FunctionTool(stop_streaming),  # Stop tool
        ]
    )

    HOW IT WORKS:
    -------------
    User: "Stop monitoring the stock"
    Agent: *calls stop_streaming(function_name="monitor_stock_price")*
    ADK: Cancels the monitor_stock_price task

    AGENT INSTRUCTIONS:
    -------------------
    Include instructions about stopping:

    instruction='''
    You can monitor things using the streaming tools.
    When the user wants to stop monitoring, use stop_streaming
    with the name of the function to stop.

    Example: stop_streaming(function_name="monitor_stock_price")
    '''

    GRACEFUL SHUTDOWN:
    ------------------
    Your streaming tool can handle cancellation:

    async def monitor_stock_price(symbol: str) -> AsyncGenerator[str, None]:
        try:
            while True:
                price = await get_price(symbol)
                yield f"Price: {price}"
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            # Cleanup
            yield f"Stopped monitoring {symbol}"

    AUTOMATIC CLEANUP:
    ------------------
    When run_live() exits:
    - All streaming tools are cancelled
    - Resources are cleaned up automatically
    """)


# =============================================================================
# Part 5: Automatic Tool Execution
# =============================================================================

def explain_automatic_execution():
    """Explain automatic tool execution in run_live()."""
    print("""
    AUTOMATIC TOOL EXECUTION
    ========================

    ADK automatically handles tool execution in run_live().

    WITHOUT ADK (Raw Live API):
    ---------------------------
    1. Receive function_call from model
    2. Execute function yourself
    3. Format function_response
    4. Send response back to model
    5. Handle errors, retries, etc.

    WITH ADK:
    ---------
    Just define tools - ADK does the rest!

    agent = Agent(
        name="my_agent",
        tools=[my_tool, another_tool],
    )

    async for event in runner.run_live(...):
        # Events include function_call and function_response
        # But ADK handles execution automatically!
        pass

    WHAT ADK DOES:
    --------------
    1. Detects function_call in model response
    2. Finds matching tool in agent
    3. Executes tool (parallel if multiple)
    4. Formats function_response
    5. Sends response back to model
    6. Handles before/after tool callbacks
    7. Yields events to your application

    TOOL EVENTS:
    ------------
    You can observe tool execution:

    async for event in runner.run_live(...):
        # Function call event
        if event.get_function_calls():
            call = event.get_function_calls()[0]
            print(f"Calling: {call.name}({call.args})")

        # Function response event
        if event.get_function_responses():
            resp = event.get_function_responses()[0]
            print(f"Result: {resp.response}")

    STREAMING TOOL EVENTS:
    ----------------------
    Streaming tools yield multiple events:

    async for event in runner.run_live(...):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    # Could be agent text OR streaming tool update
                    print(f"Update: {part.text}")

    TOOL CALLBACKS STILL WORK:
    --------------------------
    Your before/after_tool callbacks are called:

    async def before_tool(tool, args, tool_context):
        print(f"About to call {tool.name}")

    async def after_tool(tool, args, tool_context, result):
        print(f"Finished {tool.name}: {result}")

    KEY TAKEAWAY:
    -------------
    ADK transforms complex tool orchestration into simple:
    1. Define tools
    2. Iterate over run_live()
    3. Done!

    No manual function call handling needed.
    """)


# =============================================================================
# Part 6: Example Streaming Tools
# =============================================================================

# Simple streaming tool - price monitor (simulated)
async def monitor_price(
    symbol: str
) -> AsyncGenerator[str, None]:
    """Monitor price changes for a symbol (simulated).

    Args:
        symbol: The symbol to monitor (e.g., "AAPL", "BTC")

    Yields:
        Price update messages
    """
    print(f"  [Tool] Starting monitor for {symbol}")
    prices = [100, 102, 98, 105, 103, 110]

    for i, price in enumerate(prices):
        await asyncio.sleep(1)
        message = f"[{symbol}] Price update: ${price}"
        print(f"  [Tool] Yielding: {message}")
        yield message

    yield f"[{symbol}] Monitoring complete (demo ended)"


# Stop function
def stop_streaming(function_name: str) -> str:
    """Stop a streaming function.

    Args:
        function_name: Name of the function to stop

    Returns:
        Confirmation message
    """
    return f"Requested stop of {function_name}"


async def streaming_tools_demo():
    """Demonstrate streaming tools concept."""
    print("\n  Demonstrating streaming tools...")
    print("  " + "-"*50)

    # Show tool definitions
    print("\n  Streaming Tool Example:")
    print("""
    async def monitor_price(symbol: str) -> AsyncGenerator[str, None]:
        '''Monitor price for symbol.'''
        while True:
            price = await get_price(symbol)
            yield f"Price: {price}"
            await asyncio.sleep(5)
    """)

    print("\n  Video Streaming Tool Example:")
    print("""
    async def monitor_video(
        input_stream: LiveRequestQueue,  # ADK injects this!
    ) -> AsyncGenerator[str, None]:
        '''Analyze video stream.'''
        while True:
            frame = await input_stream.get()
            if frame.blob:
                result = analyze(frame.blob.data)
                yield f"Analysis: {result}"
    """)

    print("\n  Stop Function:")
    print("""
    def stop_streaming(function_name: str):
        '''Stop streaming tool by name.'''
        pass  # ADK handles this
    """)

    # Quick demo of the generator pattern
    print("\n  Quick Generator Demo:")
    print("  " + "-"*50)

    async for update in monitor_price("DEMO"):
        print(f"    Received: {update}")

    print("\n  Demo complete!")


async def main():
    print("\n" + "#"*70)
    print("# Lab 6 Exercise 5: Streaming Tools")
    print("#"*70)

    # =========================================================================
    # Part 1: Overview
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: What are Streaming Tools?")
    print("="*60)
    explain_streaming_tools()

    # =========================================================================
    # Part 2: Simple Streaming
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: Simple Streaming Tools")
    print("="*60)
    explain_simple_streaming()

    # =========================================================================
    # Part 3: Video Streaming
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: Video Streaming Tools")
    print("="*60)
    explain_video_streaming_tools()

    # =========================================================================
    # Part 4: Stopping
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Stopping Streaming Tools")
    print("="*60)
    explain_stopping()

    # =========================================================================
    # Part 5: Automatic Execution
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: Automatic Tool Execution")
    print("="*60)
    explain_automatic_execution()

    # =========================================================================
    # Part 6: Demo
    # =========================================================================
    print("\n" + "="*60)
    print("PART 6: Streaming Tools Demo")
    print("="*60)

    await streaming_tools_demo()

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Streaming Tools")
    print("#"*70)
    print("""
    STREAMING TOOLS OVERVIEW:
    -------------------------
    Tools that yield multiple results over time.
    Agent can respond to each update in real-time.

    REQUIREMENTS:
    -------------
    1. async function
    2. Return type: AsyncGenerator[T, None]
    3. Use yield for updates
    4. Only works with run_live()

    TWO TYPES:
    ----------
    1. Simple Streaming:
       async def monitor(symbol: str) -> AsyncGenerator[str, None]:
           while True:
               yield get_update()

    2. Video Streaming:
       async def analyze(
           input_stream: LiveRequestQueue  # ADK injects
       ) -> AsyncGenerator[str, None]:
           while True:
               frame = await input_stream.get()
               yield analyze(frame)

    STOPPING:
    ---------
    def stop_streaming(function_name: str):
        pass  # ADK handles stopping

    USE CASES:
    ----------
    - Price monitoring
    - Progress updates
    - Video analysis
    - Sensor data
    - Real-time notifications

    KEY BENEFIT:
    ------------
    Agent can react to continuous data streams,
    providing real-time, interactive experiences!
    """)


if __name__ == "__main__":
    asyncio.run(main())
