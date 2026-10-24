
import asyncio
from uuid import uuid4
from backend.schemas import TestRequest, TestReport
from backend.agents.tester import BrowserTester

from .schemas import TestRequest, TestReport, StepResult, TestPlan, TestStep
from .llm_service import generate_test_plan
from .agents.tester import BrowserTester
from .url_validator import validate_url


async def create_test_run(request: TestRequest) -> dict:
    run_id = str(uuid4())

    # Generate the plan without blocking the async event loop.
    try:
        plan = await asyncio.to_thread(generate_test_plan, request)
        print("Gemini successfully generated the test plan.")

    except Exception as exc:
        print(f"Gemini unavailable: {exc}")
        print("Using a temporary test plan for browser testing.")
        

        if "the-internet.herokuapp.com/login" in str(request.url):
            plan = TestPlan(
              steps=[
                    TestStep(
                        action="navigate",
                        target=str(request.url),
                        expected="Login page opens"
                    ),
                    TestStep(
                        action="fill",
                        target="#username",
                        value="tomsmith",
                        expected="Username entered"
                    ),
                    TestStep(
                        action="fill",
                        target="#password",
                        value="SuperSecretPassword!",
                        expected="Password entered"
                    ),
                    TestStep(
                        action="click",
                        target="button[type='submit']",
                        expected="Login button clicked"
                    ),
                    TestStep(
                        action="verify",
                        target="text",
                        expected="You logged into a secure area!"
                    )
                ]
            )
        else:
            plan = TestPlan(
                steps=[
                    TestStep(
                        action="navigate",
                        target=str(request.url),
                        expected="Website opens successfully"
                    ),
                    TestStep(
                        action="verify",
                        target="text",
                        expected="Learn more"
                    )
                ]
            )

    report = TestReport(
        run_id=run_id,
        status="running",
        objective=request.objective,
    )

    tester = BrowserTester()
    browser_started = False

    try:
        await tester.start()
        browser_started = True

        for index, step in enumerate(plan.steps, start=1):
            step_name = f"Step {index}: {step.action}"
            screenshot_path = ""

            try:
                if step.action == "navigate":
                    # Use the user-supplied URL for the first navigation.
                    target_url = (
                        str(request.url)
                        if index == 1
                        else step.target
                    )

                    validate_url(target_url)
                    await tester.navigate_to(target_url)
                    passed = True
                    message = f"Navigated to {target_url}"

                elif step.action == "click":
                    passed = await tester.execute_action(
                        "click", step.target
                    )
                    message = (
                        "Click action completed"
                        if passed
                        else "Click action failed"
                    )

                elif step.action == "fill":
                    if step.value is None:
                        passed = False
                        message = "Fill step has no value to enter"
                    else:
                        passed = await tester.execute_action(
                            "fill", step.target, step.value
                        )
                        message = (
                            "Input field filled"
                            if passed
                            else "Fill action failed"
                        )

                elif step.action == "verify":
                    if step.target.lower() == "url":
                        passed = await tester.verify_assertion(
                            "url_contains", step.expected
                        )
                    else:
                        passed = await tester.verify_assertion(
                            "text_visible", step.expected
                        )

                    message = (
                        f"Expected result found: {step.expected}"
                        if passed
                        else f"Expected result not verified: {step.expected}"
                    )

                else:
                    passed = False
                    message = f"Unsupported action: {step.action}"

                
                try:
                    screenshot_path = await tester.runner.capture_screenshot(
                        f"{run_id}_step_{index}"
                    )   
                except Exception as screenshot_exc:
                    print(f"Screenshot failed for {step_name}: {screenshot_exc}")

                report.steps.append(
                    StepResult(
                        name=step_name,
                        status="passed" if passed else "failed",
                        message=message,
                    )
                )


            except Exception as exc:
                report.steps.append(
                    StepResult(
                        name=step_name,
                        status="failed",
                        message=f"Step execution error: {str(exc)}",
                    )
                )
                report.issues.append(f"{step_name} failed")

        report.status = "completed"

    except Exception as exc:
        report.status = "error"
        report.issues.append(f"Test execution error: {str(exc)}")

    finally:
        if browser_started:
            try:
                await tester.close()
            except Exception as exc:
                report.issues.append(
                    f"Browser cleanup error: {str(exc)}"
                )

    return {
        "run_id": run_id,
        "status": report.status,
        "plan": plan,
        "report": report,
    }