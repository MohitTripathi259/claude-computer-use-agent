"""
Test if computer_20241022 is a valid Anthropic tool type
"""
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Test 1: Try computer_20241022 (native type)
print("=" * 60)
print("TEST 1: Using computer_20241022 (Anthropic's official type)")
print("=" * 60)

try:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=[
            {
                "type": "computer_20241022",
                "name": "computer",
                "display_width_px": 1024,
                "display_height_px": 768,
                "display_number": 1
            }
        ],
        messages=[
            {"role": "user", "content": "Take a screenshot"}
        ]
    )
    print("✅ SUCCESS: computer_20241022 is a valid type!")
    print(f"Response: {response.content}")
except Exception as e:
    print(f"❌ FAILED: {e}")
    print(f"Error type: {type(e).__name__}")

# Test 2: Try custom type (what we're currently using)
print("\n" + "=" * 60)
print("TEST 2: Using custom type (our current approach)")
print("=" * 60)

try:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=[
            {
                "type": "custom",
                "name": "computer",
                "description": "Control computer screen, mouse, and keyboard",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["screenshot", "mouse_move", "left_click"]
                        },
                        "coordinate": {"type": "array"}
                    },
                    "required": ["action"]
                }
            }
        ],
        messages=[
            {"role": "user", "content": "Take a screenshot"}
        ]
    )
    print("✅ SUCCESS: custom type works!")
    print(f"Response: {response.content}")
except Exception as e:
    print(f"❌ FAILED: {e}")

print("\n" + "=" * 60)
print("CONCLUSION")
print("=" * 60)
print("If TEST 1 passes: We should use computer_20241022")
print("If TEST 1 fails: We correctly used custom type")
