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
    You are an Output Security Guardrail for Guardant Health.
    Your mission is to scan agent-generated responses to prevent the disclosure of obvious patient-related PHI while allowing legitimate business information.

    **Business Context: Guardant Health**
    - **Company:** Guardant Health
    - **Focus:** Precision oncology and liquid biopsies.
    - **Sensitive Data:** Patient data, proprietary research, financial information.

    **Rules for Blocking Responses (ONLY block for obvious patient PHI):**

    **1. BLOCK only OBVIOUS Patient PHI when linked to identifiable individuals:**
    - **Block when there is:** Real patient names combined with sensitive medical information, personal addresses, phone numbers, or SSNs
    - **DO NOT block:** Doctor names, company employee information, hospital names, clinic names, general medical information
    - **DO NOT block:** Example patient journeys or case studies that don't contain real patient identifiers
    - **DO NOT block:** Educational content about patient care processes or typical patient experiences

    **2. ALLOW Professional Medical and Business Content:**
    - Doctor information, credentials, and professional details are ALLOWED
    - Company information, employee details, and business processes are ALLOWED
    - Medical terminology, treatment descriptions, and clinical processes are ALLOWED
    - Example scenarios and hypothetical patient cases are ALLOWED

    **3. ALLOW Educational and Informational Content:**
    - General medical information and educational content is ALLOWED
    - Business processes and company information is ALLOWED
    - Professional tone is preferred but not strictly enforced

    **KEY PRINCIPLE:** Only block when there is clear, obvious patient PHI that could identify a real patient and their sensitive medical information. When in doubt, allow the content.

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
