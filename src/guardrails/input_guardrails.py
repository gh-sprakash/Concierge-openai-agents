"""
Input Guardrails - Pre-processing security checks
"""

from typing import List
from pydantic import BaseModel, Field
from agents import (
    Agent, 
    Runner, 
    input_guardrail, 
    GuardrailFunctionOutput,
    RunContextWrapper,
    ModelSettings
)

# Pydantic models for structured output
class InputSecurityCheck(BaseModel):
    """Security analysis of user input"""
    is_allowed: bool = Field(description="Whether the query is allowed to proceed")
    reasoning: str = Field(description="Explanation for the decision")
    violated_policies: List[str] = Field(description="List of violated policies, if any")

# Input Guardrail Agent
input_guardrail_agent = Agent(
    name="InputGuardrailAgent",
    instructions="""
    You are a flexible Input Security Guardrail for Guardant Health, a precision oncology company.
    Your mission is to be permissive and only block clearly inappropriate or completely off-topic requests.

    **Business Context: Guardant Health**
    - **Company:** Guardant Health
    - **Focus:** Precision oncology, liquid biopsies (blood-based cancer tests).
    - **Products:** Guardant360, GuardantOMNI, Guardant Reveal, LUNAR Program.
    - **Technology:** Analyzes circulating tumor DNA (ctDNA).
    - **Goal:** Improve cancer detection, treatment selection, and monitoring.

    **PERMISSIVE Approach - ALLOW Most Queries:**

    **1. ALWAYS ALLOW (is_allowed = True):**
    - Basic greetings and conversational starters (e.g., "Hi", "Hello", "How are you?")
    - ALL business-related queries including CRMs, portals, sales tools, marketing, operations, etc.
    - Guardant Health products, services, technology, competitors, partnerships
    - Healthcare, oncology, genomics, medical topics
    - Healthcare professionals information (names, titles, contact info)
    - Company information, policies, procedures, workflows
    - Any query that could reasonably be related to work at Guardant Health
    - Technical questions about systems, software, processes
    - Questions about training materials, documentation, knowledge base content

    **2. ONLY BLOCK Obvious Off-Topic Content (is_allowed = False):**
    - **Patient PII:** Requests for specific patient personal information (names, addresses, SSNs, etc.)
    - **Completely Unrelated Topics:** Jokes, entertainment, travel planning, cooking recipes, sports, weather, personal life advice
    - **Harmful Content:** Requests for illegal activities, offensive content, or harassment
    
    **Key Principle:** When in doubt, ALLOW the query. Only block if it's clearly inappropriate or completely unrelated to any possible business context.
    
    Provide a clear reasoning for your decision and list any violated policies.
    """,
    output_type=InputSecurityCheck,
    model="gpt-4o-mini",
    model_settings=ModelSettings(temperature=0.0)
)

@input_guardrail
async def input_security_guardrail(
    ctx: RunContextWrapper,
    agent: Agent,
    input_data: str
) -> GuardrailFunctionOutput:
    """
    An input guardrail that uses an agent to check for PII, brand compliance, and domain constraints.
    """
    try:
        result = await Runner.run(
            input_guardrail_agent,
            f"Analyze the following user query: '{input_data}'"
        )
        security_check = result.final_output_as(InputSecurityCheck)

        return GuardrailFunctionOutput(
            tripwire_triggered=not security_check.is_allowed,
            output_info=security_check.model_dump()
        )
    except Exception as e:
        # Fail-safe: block the query if the guardrail fails
        return GuardrailFunctionOutput(
            tripwire_triggered=True,
            output_info={"error": str(e), "is_allowed": False}
        )
