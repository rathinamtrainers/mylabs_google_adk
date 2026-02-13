"""Travel assistant agent for evaluation exercises."""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool


# --- Tool functions ---

def search_flights(origin: str, destination: str, date: str) -> dict:
    """Search for available flights."""
    flights = [
        {"flight_id": "FL001", "price": 299, "departure": "08:00", "arrival": "11:00", "airline": "SkyAir"},
        {"flight_id": "FL002", "price": 399, "departure": "14:00", "arrival": "17:00", "airline": "CloudJet"},
        {"flight_id": "FL003", "price": 249, "departure": "20:00", "arrival": "23:00", "airline": "SkyAir"},
    ]
    return {"origin": origin, "destination": destination, "date": date, "flights": flights}


def get_flight_details(flight_id: str) -> dict:
    """Get detailed flight information."""
    details = {
        "FL001": {"flight_id": "FL001", "price": 299, "class": "economy", "baggage": "1 carry-on", "meal": "snack"},
        "FL002": {"flight_id": "FL002", "price": 399, "class": "economy+", "baggage": "1 checked", "meal": "full"},
        "FL003": {"flight_id": "FL003", "price": 249, "class": "economy", "baggage": "1 carry-on", "meal": "none"},
    }
    return details.get(flight_id, {"error": f"Flight {flight_id} not found"})


def book_flight(flight_id: str, passenger_name: str, email: str) -> dict:
    """Book a flight for a passenger."""
    return {
        "success": True,
        "confirmation_number": f"CONF-{flight_id}-001",
        "flight_id": flight_id,
        "passenger": passenger_name,
        "email": email,
    }


def cancel_booking(confirmation_number: str) -> dict:
    """Cancel a flight booking."""
    return {
        "success": True,
        "message": f"Booking {confirmation_number} cancelled. Refund will be processed in 5-7 days.",
    }


def get_weather(city: str) -> dict:
    """Get weather information for a city."""
    weather = {
        "new york": {"temp_f": 35, "condition": "cloudy", "humidity": 65},
        "los angeles": {"temp_f": 72, "condition": "sunny", "humidity": 30},
        "chicago": {"temp_f": 28, "condition": "snowy", "humidity": 70},
        "miami": {"temp_f": 80, "condition": "sunny", "humidity": 75},
    }
    return weather.get(city.lower(), {"error": f"Weather data not available for {city}"})


# --- Agent definition ---

root_agent = LlmAgent(
    name="TravelAgent",
    model="gemini-2.0-flash",
    instruction="""You are a travel assistant. Help users search for flights, book tickets, and get travel information.

    Workflow for booking:
    1. Search for flights using search_flights
    2. If user wants details, use get_flight_details
    3. To book, use book_flight with passenger name and email

    For cancellations, use cancel_booking with the confirmation number.
    You can also check weather at destinations using get_weather.

    Be helpful, concise, and always confirm details before booking.""",
    tools=[
        FunctionTool(func=search_flights),
        FunctionTool(func=get_flight_details),
        FunctionTool(func=book_flight),
        FunctionTool(func=cancel_booking),
        FunctionTool(func=get_weather),
    ],
)
