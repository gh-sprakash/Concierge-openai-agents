"""
Security Guardrails - PII protection and content filtering
Implements strict security checks to prevent inappropriate queries and protect sensitive information
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from agents import (
    Agent, 
    Runner, 
    input_guardrail, 
    output_guardrail,
    GuardrailFunctionOutput,
    RunContextWrapper,
    ModelSettings
)


class SecurityCheckResult(BaseModel):
    """Security analysis result"""
    contains_pii: bool = Field(description="Whether the content contains PII requests")
    contains_inappropriate_content: bool = Field(description="Whether content is inappropriate for business")
    is_business_appropriate: bool = Field(description="Whether the content is business-appropriate")
    allowed: bool = Field(description="Whether the request should be allowed")
    reasoning: str = Field(description="Explanation of the decision")
    violated_policies: List[str] = Field(description="List of violated policies")


class PIIDetectionResult(BaseModel):
    """PII detection specific result"""
    has_pii_request: bool
    pii_types_detected: List[str]
    confidence_score: float


# Security analysis agent - uses fastest model for quick responses
security_agent = Agent(
    name="Security Guardrail Checker",
    instructions="""
    You are a STRICT security checker for a business sales application.
    
    🛡️ **PRIMARY MISSION**: Protect sensitive information and ensure business-appropriate usage.
    
    ❌ **IMMEDIATELY BLOCK (set allowed=False) these categories:**
    
    1. **PII REQUESTS**:
       - Phone numbers: "phone number", "contact number", "call", "telephone"
       - Email addresses: "email", "email address", "@", "contact email"  
       - Social Security: "SSN", "social security", "social security number"
       - Personal addresses: "home address", "personal address", "mailing address"
       - Any request for personal contact information
    
    2. **INAPPROPRIATE CONTENT**:
       - Math problems: "solve", "calculate", "what is X + Y", "math", mathematical expressions
       - Jokes and humor: "tell me a joke", "funny story", "make me laugh", humor requests
       - Personal questions: unrelated to business, personal life questions
       - Entertainment: games, trivia, non-business content
    
    3. **OFF-TOPIC BUSINESS QUERIES**:
       - Politics, religion, personal opinions
       - Non-healthcare/sales related topics
       - Requests outside sales assistant scope
    
    ✅ **ALLOW (set allowed=True) these business queries:**
    - Doctor names for business: "Dr. Julie", "Dr. Smith", "Dr. Shafique"
    - Order information: "What tests did Dr. X order?", "order status", "compliance"
    - Engagement data: "engagement history", "talking points", "meetings"
    - Contact relationships: "Who has Dr. X contacted?" (this is business relationship mapping)
    - Product information: "Guardant360 features", "product specifications"
    - Business analytics: "sales trends", "performance metrics"
    - Training materials: "product training", "sales training"
    
    🔍 **ANALYSIS PROCESS**:
    1. Scan for PII-related keywords (phone, email, SSN, address)
    2. Check for inappropriate content (math, jokes, entertainment)
    3. Verify business relevance and appropriateness
    4. List specific policy violations
    5. Provide clear reasoning for decision
    
    **IMPORTANT**: "Who has Dr. X contacted?" is ALLOWED - this asks about business relationships, not personal PII.
    
    Be STRICT but allow legitimate business queries. When in doubt, err on the side of security.
    """,
    output_type=SecurityCheckResult,
    model="gpt-4o-mini",  # Fast model for quick guardrail responses
    model_settings=ModelSettings(temperature=0.0, max_tokens=500)  # Deterministic, concise
)


@input_guardrail
async def strict_security_guardrail(
    ctx: RunContextWrapper,
    agent: Agent,
    input_data: str
) -> GuardrailFunctionOutput:
    """
    🛡️ Strict Security Input Guardrail
    
    This guardrail runs before the main agent processes the query.
    It blocks requests that:
    - Ask for PII (phone, email, SSN)
    - Request inappropriate content (math, jokes)
    - Are not business-appropriate
    
    Returns GuardrailFunctionOutput with tripwire_triggered=True if blocked.
    """
    print("🛡️ Security Guardrail: Analyzing input...")
    
    try:
        # Run security analysis
        result = await Runner.run(
            security_agent, 
            f"Analyze this user query for security violations: '{input_data}'",
            context=ctx.context
        )
        
        security_check = result.final_output_as(SecurityCheckResult)
        
        print(f"🛡️ Security Check Result: allowed={security_check.allowed}")
        print(f"🛡️ Violations: {security_check.violated_policies}")
        
        return GuardrailFunctionOutput(
            output_info=security_check.model_dump(),
            tripwire_triggered=not security_check.allowed
        )
        
    except Exception as e:
        print(f"❌ Security guardrail error: {e}")
        # Fail-safe: block on error
        return GuardrailFunctionOutput(
            output_info={"error": str(e), "allowed": False},
            tripwire_triggered=True
        )


@input_guardrail 
async def pii_protection_guardrail(
    ctx: RunContextWrapper,
    agent: Agent,
    input_data: str
) -> GuardrailFunctionOutput:
    """
    🔒 PII Protection Guardrail (Alternative/Additional)
    
    Focused specifically on detecting and blocking PII requests.
    Can be used alongside or instead of the main security guardrail.
    """
    print("🔒 PII Protection: Scanning for sensitive data requests...")
    
    # Simple keyword-based PII detection
    input_lower = str(input_data).lower()
    
    pii_indicators = {
        'phone': ['phone', 'telephone', 'contact number', 'call'],
        'email': ['email', '@', 'contact email', 'email address'],
        'ssn': ['ssn', 'social security', 'social security number'],
        'address': ['address', 'home address', 'mailing address']
    }
    
    detected_pii_types = []
    for pii_type, keywords in pii_indicators.items():
        if any(keyword in input_lower for keyword in keywords):
            detected_pii_types.append(pii_type)
    
    has_pii_request = len(detected_pii_types) > 0
    confidence = 1.0 if has_pii_request else 0.0
    
    pii_result = PIIDetectionResult(
        has_pii_request=has_pii_request,
        pii_types_detected=detected_pii_types,
        confidence_score=confidence
    )
    
    print(f"🔒 PII Detection: {detected_pii_types} (confidence: {confidence})")
    
    return GuardrailFunctionOutput(
        output_info=pii_result.model_dump(),
        tripwire_triggered=has_pii_request
    )


@output_guardrail
async def response_safety_guardrail(
    ctx: RunContextWrapper,
    agent: Agent,
    output: str
) -> GuardrailFunctionOutput:
    """
    🛡️ Output Safety Guardrail
    
    Scans agent responses to ensure they don't accidentally include:
    - Personal contact information
    - Inappropriate content
    - Sensitive business data that should be filtered
    
    This is a secondary safety check on the agent's response.
    """
    print("🛡️ Output Safety: Scanning response...")
    
    output_str = str(output)
    
    # Look for potential PII patterns in output
    pii_patterns = {
        'phone_pattern': r'\b\d{3}-\d{3}-\d{4}\b',  # XXX-XXX-XXXX format
        'email_pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'ssn_pattern': r'\b\d{3}-\d{2}-\d{4}\b'  # XXX-XX-XXXX format
    }
    
    import re
    violations = []
    for pattern_name, pattern in pii_patterns.items():
        if re.search(pattern, output_str):
            violations.append(f"Potential {pattern_name} detected in response")
    
    has_violations = len(violations) > 0
    
    if has_violations:
        print(f"⚠️ Output Safety Violations: {violations}")
    
    return GuardrailFunctionOutput(
        output_info={
            "violations": violations,
            "safe": not has_violations
        },
        tripwire_triggered=has_violations
    )


def create_custom_policy_guardrail(policy_name: str, policy_rules: List[str]):
    """
    🏭 Factory function to create custom policy guardrails
    
    Args:
        policy_name: Name of the policy (e.g., "HIPAA", "SOX", "GDPR")
        policy_rules: List of rule descriptions
    
    Returns:
        Configured guardrail function
    """
    
    @input_guardrail
    async def custom_policy_guardrail(
        ctx: RunContextWrapper,
        agent: Agent,
        input_data: str
    ) -> GuardrailFunctionOutput:
        
        policy_agent = Agent(
            name=f"{policy_name} Policy Checker",
            instructions=f"""
            You are checking compliance with {policy_name} policy.
            
            Policy Rules:
            {chr(10).join([f"• {rule}" for rule in policy_rules])}
            
            Analyze the user query and determine if it violates any of these rules.
            """,
            output_type=SecurityCheckResult,
            model="gpt-4o-mini"
        )
        
        result = await Runner.run(
            policy_agent,
            f"Check this query against {policy_name} policy: '{input_data}'"
        )
        
        check = result.final_output_as(SecurityCheckResult)
        
        return GuardrailFunctionOutput(
            output_info=check.model_dump(),
            tripwire_triggered=not check.allowed
        )
    
    return custom_policy_guardrail


# Export main components
__all__ = [
    'strict_security_guardrail',
    'pii_protection_guardrail', 
    'response_safety_guardrail',
    'create_custom_policy_guardrail',
    'SecurityCheckResult',
    'PIIDetectionResult'
]