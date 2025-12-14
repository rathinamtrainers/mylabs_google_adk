"""
Lab 8 - Server: Weather Agent
=============================

A standalone weather agent exposed via A2A protocol.
Provides mock weather information for demonstration.

Run: uv run python server/weather_agent.py

The agent will be available at:
- A2A endpoint: http://localhost:8002/
- Agent card: http://localhost:8002/.well-known/agent-card.json
"""

import uvicorn
from google.adk.agents import LlmAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a


# =============================================================================
# Weather Tools
# =============================================================================

# Mock weather data for demonstration
MOCK_WEATHER = {
    "new york": {"temp": 72, "condition": "Partly Cloudy", "humidity": 65},
    "los angeles": {"temp": 85, "condition": "Sunny", "humidity": 40},
    "chicago": {"temp": 68, "condition": "Windy", "humidity": 55},
    "miami": {"temp": 88, "condition": "Humid", "humidity": 80},
    "seattle": {"temp": 62, "condition": "Rainy", "humidity": 75},
    "denver": {"temp": 70, "condition": "Clear", "humidity": 30},
    "london": {"temp": 58, "condition": "Overcast", "humidity": 70},
    "tokyo": {"temp": 75, "condition": "Clear", "humidity": 60},
    "paris": {"temp": 65, "condition": "Mild", "humidity": 55},
    "sydney": {"temp": 68, "condition": "Sunny", "humidity": 50},
}


def get_weather(city: str) -> dict:
    """Get current weather for a city.

    Args:
        city: Name of the city (case-insensitive)

    Returns:
        Weather data including temperature (F), condition, and humidity
    """
    city_lower = city.lower()
    if city_lower in MOCK_WEATHER:
        data = MOCK_WEATHER[city_lower]
        return {
            "city": city,
            "temperature_f": data["temp"],
            "temperature_c": round((data["temp"] - 32) * 5 / 9, 1),
            "condition": data["condition"],
            "humidity_percent": data["humidity"],
        }
    else:
        # Return generic weather for unknown cities
        return {
            "city": city,
            "temperature_f": 70,
            "temperature_c": 21.1,
            "condition": "Unknown",
            "humidity_percent": 50,
            "note": "Weather data not available for this city, showing defaults",
        }


def get_forecast(city: str, days: int = 3) -> list:
    """Get weather forecast for upcoming days.

    Args:
        city: Name of the city
        days: Number of days to forecast (1-7)

    Returns:
        List of daily forecasts
    """
    days = min(max(days, 1), 7)  # Clamp to 1-7

    current = get_weather(city)
    base_temp = current["temperature_f"]

    forecasts = []
    for i in range(days):
        # Simple mock: vary temperature slightly each day
        temp_var = (i * 3) % 10 - 5
        forecasts.append({
            "day": i + 1,
            "temperature_f": base_temp + temp_var,
            "condition": current["condition"],
        })

    return {
        "city": city,
        "forecast_days": days,
        "forecasts": forecasts,
    }


# =============================================================================
# Weather Agent
# =============================================================================

weather_agent = LlmAgent(
    name="WeatherAgent",
    model="gemini-2.0-flash",
    description="A weather specialist that provides current weather conditions "
                "and forecasts for cities around the world.",
    instruction="""You are a weather specialist agent.
    Use your tools to get weather information:
    - get_weather(city): Get current weather for a city
    - get_forecast(city, days): Get forecast for upcoming days

    Always use tools to get weather data - don't make up weather.
    Present weather information in a friendly, readable format.
    Include both Fahrenheit and Celsius temperatures when relevant.""",
    tools=[get_weather, get_forecast],
)


# =============================================================================
# A2A Server Setup
# =============================================================================

# Convert agent to A2A service
app = to_a2a(agent=weather_agent, host="localhost", port=8002)


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("Starting Weather Agent A2A Server")
    print("=" * 50)
    print("\nEndpoints:")
    print("  A2A:        http://localhost:8002/")
    print("  Agent Card: http://localhost:8002/.well-known/agent-card.json")
    print("\nAvailable cities:")
    for city in MOCK_WEATHER.keys():
        print(f"  - {city.title()}")
    print("\nPress Ctrl+C to stop\n")

    uvicorn.run(app, host="0.0.0.0", port=8002)
