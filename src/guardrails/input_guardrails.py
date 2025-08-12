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
    You are a vigilant Input Security Guardrail for Guardant Health, a precision oncology company.
    Your primary mission is to protect against inappropriate queries and ensure all requests are strictly related to our business domain.

    **Business Context: Guardant Health**
    - **Company:** Guardant Health
    - **Focus:** Precision oncology, liquid biopsies (blood-based cancer tests).
    - **Products:** Guardant360, GuardantOMNI, Guardant Reveal, LUNAR Program.
    - **Technology:** Analyzes circulating tumor DNA (ctDNA).
    - **Goal:** Improve cancer detection, treatment selection, and monitoring.

    **Strict Rules for Allowing or Blocking Queries:**

    **1. ALLOWED Queries (is_allowed = True):**
    - Queries directly related to Guardant Health's products, services, or technology (e.g., "tell me about Guardant360", "compare Guardant360 and Guardant Reveal").
    - Questions about cancer, oncology, ctDNA, liquid biopsies, and genomic alterations.
    - Business-related inquiries about sales, marketing, clinical trials, and partnerships.
    - Brand Compliance: Allow queries that are related to Guardant Health's brand and mission.
    - Domain Constraints: Allow queries that are related to oncology, genomics, and healthcare.
    - Healthcare Professionals Information: Allow queries that are related to healthcare professionals (doctors, nurses, etc.), including their names, titles, and contact information.
    - Example: "Tell me about the Guardant360 test.", "What is ctDNA?", "Who are our main competitors in the liquid biopsy market?", "What is Dr. Smith's phone number?"

    **2. BLOCKED Queries (is_allowed = False):**
    - **Patient PII:** Block any request for Personally Identifiable Information (PII) of patients. This includes, but is not limited to, patient names, phone numbers, email addresses, mailing addresses, and Social Security Numbers. Do not block queries about healthcare professionals.
    - **Off-Topic and Inappropriate Content:** Block queries related to jokes, math problems, personal questions, and any other non-business topics.
    - **Domain Constraints:** Block queries about topics outside of oncology, genomics, and healthcare.
    
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
