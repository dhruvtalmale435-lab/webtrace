
import os

from dotenv import load_dotenv

from .schemas import TestPlan, TestRequest


# Load environment variables from the project root
load_dotenv()


def generate_test_plan(request: TestRequest) -> TestPlan:
    """Generate a structured test plan using Gemini AI."""

    # Imported lazily so the API still starts (with the fallback test plan)
    # on machines where google-genai is not installed.
    from google import genai
    from google.genai import types

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Check your root .env file."
        )

    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are an expert web application QA tester.

    Website URL: {request.url}
    Testing objective: {request.objective}

    Create a practical test plan containing 2 to 10 steps.

       Rules:
    - Use only these actions: navigate, click, fill, verify.
    - Every step must have action, target, and expected.
    - The first step must navigate to the supplied website URL.
    - For click and fill, target must be a CSS selector, not a natural-language description.
    - For fill, provide the input text in the value field.
    - For verify, target must be "text" or "url".
    - For text verification, expected must be the text to find on the page.
    - For URL verification, expected must be the URL substring to check.
    - Do not invent login credentials or submit purchases or payments.
    - Do not claim that tests have already been executed.
    - Generate a plan only. Do not execute browser actions.
    """

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=TestPlan,
            temperature=0.2,
        ),
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty test plan.")

    return TestPlan.model_validate_json(response.text)
