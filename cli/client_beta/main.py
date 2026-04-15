import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

def main():
    load_dotenv()
    api_key =  os.environ.get("GEMINI_API_KEY")

    client = genai.Client(api_key=api_key)

    if len(sys.argv) < 2:
        print("Usage: python main.py <prompt>")
        return

    if len(sys.argv) == 3 and sys.argv[2] == "--verbose":
        verbose_flag = True
    else:
        verbose_flag = False
        

    prompt = sys.argv[1]

    messages = [types.Content(role="user",parts=[types.Part(text=prompt)]),]

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=messages,
    )

    print(response.text)

    if response is None or response.usage_metadata is None:
        print("response is malformed")
        return

    if verbose_flag:
        print(f"\nuser prompt: {prompt}\n")
        print(f"Prompt tokens {response.usage_metadata.prompt_token_count}\n")
        print(f"Response tokens {response.usage_metadata.candidates_token_count}\n")

main()