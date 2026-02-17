"""Test OpenRouter API key and model availability."""
from openai import OpenAI
import json

api_key = "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"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# Test with different models
models_to_test = [
    "google/gemini-3-flash-preview",  # Current config
    "google/gemini-flash-1.5",  # Correct name?
    "google/gemini-pro-1.5",  # Alternative
    "anthropic/claude-3.5-sonnet",  # Fallback
]

print("Testing OpenRouter API...")
print(f"API Key: {api_key[:20]}...")
print()

for model in models_to_test:
    print(f"Testing model: {model}")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hello, respond with 'OK'"}],
            max_tokens=10
        )
        result = response.choices[0].message.content
        print(f"  SUCCESS: {result}")
        break
    except Exception as e:
        error_str = str(e)
        if "401" in error_str:
            print(f"  401 Authentication Error")
            print(f"  Message: User not found (API key invalid)")
        elif "404" in error_str:
            print(f"  Model not found (404)")
        else:
            print(f"  Error: {error_str[:150]}")
    print()

print("\nDIAGNOSIS:")
print("The OpenRouter API key is returning '401 - User not found'")
print("This means:")
print("  1. The API key is invalid or expired")
print("  2. The account associated with this key doesn't exist")
print("  3. The API key may have been revoked")
print("\nSOLUTION:")
print("  1. Visit https://openrouter.ai/")
print("  2. Log in or create a new account")
print("  3. Go to Keys section")
print("  4. Generate a new API key")
print("  5. Update .env file with the new key")
