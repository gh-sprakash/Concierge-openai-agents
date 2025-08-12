"""
Output Guardrails - Post-processing security checks for agent responses
"""

from typing import List
from pydantic import BaseModel, Field
from agents import (
    Agent, 
    Runner, 
    output_guardrail, 
    GuardrailFunctionOutput,
    RunContextWrapper,
    ModelSettings
)

# Pydantic models for structured output
class OutputSecurityCheck(BaseModel):
    """Security analysis of agent output"""
    is_safe: bool = Field(description="Whether the output is safe to return to the user")
    reasoning: str = Field(description="Explanation for the decision")
    violated_policies: List[str] = Field(description="List of violated policies, if any")

# Output Guardrail Agent
output_guardrail_agent = Agent(
    name="OutputGuardrailAgent",
    instructions="""
    You are a vigilant Output Security Guardrail for Guardant Health.
    Your mission is to scan agent-generated responses to prevent the accidental disclosure of sensitive information and ensure brand safety.

    **Business Context: Guardant Health**
    - **Company:** Guardant Health
    - **Focus:** Precision oncology and liquid biopsies.
    - **Sensitive Data:** Patient data, proprietary research, financial information.

    **Strict Rules for Sanitizing and Blocking Responses:**

    **1. SCAN for and BLOCK any Patient Personally Identifiable Information (PII):**
    - **Do not allow:** Phone numbers, email addresses, Social Security Numbers, personal addresses.
    - If PII is detected, block the response (is_safe = False).

    **2. ENSURE Brand and Domain Compliance:**
    - The response should be consistent with Guardant Health's brand and mission.
    - Block any content that is off-brand, speculative, or makes unsubstantiated claims.
    - Block any information that falls outside the approved domains of oncology, genomics, and diagnostics.

    **3. PREVENT Inappropriate or Unprofessional Content:**
    - The tone should always be professional.
    - Block any informal language, jokes, or non-business-related content.

    Provide a clear reasoning for your decision and list any violated policies.
    """,
    output_type=OutputSecurityCheck,
    model="gpt-4o-mini",
    model_settings=ModelSettings(temperature=0.0)
)

@output_guardrail
async def output_security_guardrail(
    ctx: RunContextWrapper,
    agent: Agent,
    output: str
) -> GuardrailFunctionOutput:
    """
    An output guardrail that uses an agent to scan the response for PII and other sensitive content.
    """
    try:
        result = await Runner.run(
            output_guardrail_agent,
            f"Analyze the following agent response: '{output}'"
        )
        security_check = result.final_output_as(OutputSecurityCheck)

        return GuardrailFunctionOutput(
            tripwire_triggered=not security_check.is_safe,
            output_info=security_check.model_dump()
        )
    except Exception as e:
        # Fail-safe: block the response if the guardrail fails
        return GuardrailFunctionOutput(
            tripwire_triggered=True,
            output_info={"error": str(e), "is_safe": False}
        )
