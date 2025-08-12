"""
Function Tools - Business data source integrations
Implements @function_tool decorated functions for Salesforce, Veeva, Tableau, and Knowledge Base
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from agents import function_tool, RunContextWrapper

# Import data sources
from ..data.salesforce import salesforce_data
from ..data.veeva import veeva_data  
from ..data.tableau import tableau_data
from ..knowledge.bedrock_kb import knowledge_base


# Data models for structured responses
class OrderInfo(BaseModel):
    """Structured order information from Salesforce"""
    doctor: str
    total_orders: int
    total_value: float
    recent_orders: List[Dict[str, Any]]
    status_summary: Dict[str, int]


class EngagementInfo(BaseModel):
    """Structured engagement information from Veeva"""
    doctor: str
    last_engagement_date: str
    engagement_type: str
    outcome: str
    talking_points: List[str]
    contacts_made: List[Dict[str, Any]]


# Structured KB result with sources for citations
class KnowledgeResult(BaseModel):
    """Structured knowledge base retrieval result"""
    document_chunks: List[str]
    sources: List[Dict[str, Any]] = []
    query: str = ""

# Context class for sharing data between tools
class SalesContext:
    """Sales context shared across all tools"""
    def __init__(self, user_name: str = "Sales Rep", territory: str = "Northeast", user_role: str = "Sales Representative"):
        self.user_name = user_name
        self.territory = territory
        self.user_role = user_role


@function_tool
async def query_salesforce_tool(
    ctx: RunContextWrapper[SalesContext],
    doctor_name: Optional[str] = None
) -> OrderInfo:
    """
    🔧 Salesforce Tool: Query doctor orders and compliance information
    
    This tool retrieves order information from Salesforce CRM, including:
    - Order history and status
    - Financial totals and summaries
    - Recent order activity
    - Stark Law compliance data (when applicable)
    
    Args:
        doctor_name: Specific doctor name to filter orders (optional)
        
    Returns:
        OrderInfo: Structured order and compliance information
    """
    print(f"🔧 Salesforce Tool Called: doctor={doctor_name}")
    
    # Get order summary from data source
    order_summary = salesforce_data.get_order_summary(doctor_name)
    
    return OrderInfo(
        doctor=order_summary["doctor"],
        total_orders=order_summary["total_orders"],
        total_value=order_summary["total_value"],
        recent_orders=order_summary["recent_orders"],
        status_summary=order_summary["status_summary"]
    )


@function_tool
async def query_veeva_tool(
    ctx: RunContextWrapper[SalesContext],
    doctor_name: str
) -> EngagementInfo:
    """
    🔧 Veeva Tool: Query healthcare professional engagement data
    
    This tool retrieves engagement information from Veeva CRM, including:
    - Latest engagement activities
    - Talking points and outcomes
    - Contact information and relationship mapping
    - Next steps and follow-up plans
    
    Args:
        doctor_name: Name of the healthcare professional
        
    Returns:
        EngagementInfo: Structured engagement and contact information
    """
    print(f"🔧 Veeva Tool Called: doctor={doctor_name}")
    
    # Get latest engagement info from data source
    engagement_info = veeva_data.get_latest_engagement(doctor_name)
    
    return EngagementInfo(
        doctor=engagement_info["doctor"],
        last_engagement_date=engagement_info["last_engagement_date"],
        engagement_type=engagement_info["engagement_type"],
        outcome=engagement_info["outcome"],
        talking_points=engagement_info["talking_points"],
        contacts_made=engagement_info["contacts_made"]
    )


@function_tool
async def query_knowledge_tool(
    ctx: RunContextWrapper[SalesContext],
    query: str
) -> KnowledgeResult:
    """
    🔧 Knowledge Base Tool: Product information and training materials
    
    This tool retrieves relevant document chunks from the AWS Bedrock Knowledge Base for:
    - Product features and specifications
    - Clinical studies and evidence
    - Training materials and best practices
    - Competitive information
    - Regulatory and compliance guidance
    
    Args:
        query: Question or topic to search for in the knowledge base
        
    Returns:
        KnowledgeResult: Raw document chunks and sources for the main agent to process
    """
    print(f"🔧 Knowledge Base Tool Called: query={query}")
    
    # Retrieve document chunks directly (no generation)
    kb_result = knowledge_base.retrieve_documents(query)
    
    return KnowledgeResult(
        document_chunks=kb_result.get("chunks", []),
        sources=kb_result.get("sources", []),
        query=query
    )


@function_tool
async def query_tableau_tool(
    ctx: RunContextWrapper[SalesContext],
    analysis_type: str = "trends"
) -> str:
    """
    🔧 Tableau Tool: Analytics and business intelligence
    
    This tool provides business analytics and insights from Tableau, including:
    - Test ordering trends and growth metrics
    - Regional performance comparisons
    - Customer satisfaction scores
    - Product performance analytics
    - Actionable business insights
    
    Args:
        analysis_type: Type of analysis to perform (trends, regional, insights)
        
    Returns:
        str: Formatted analytics report
    """
    print(f"🔧 Tableau Tool Called: type={analysis_type}")
    
    if analysis_type.lower() == "insights":
        insights = tableau_data.get_performance_insights()
        return "\n".join([f"• {insight}" for insight in insights])
    elif analysis_type.lower() == "regional":
        regions = tableau_data.get_regional_performance()
        result = "🌎 Regional Performance Summary:\n\n"
        for region in regions:
            result += f"**{region['region']}:**\n"
            result += f"• Orders: {region['total_orders']:,}\n"
            result += f"• Revenue: ${region['revenue']:,}\n"  
            result += f"• Growth: {region['growth']}\n"
            result += f"• Key Accounts: {region['key_accounts']}\n\n"
        return result
    else:
        # Default to trends analysis
        return tableau_data.get_analytics_summary()


@function_tool
async def query_compliance_tool(
    ctx: RunContextWrapper[SalesContext],
    doctor_name: str
) -> str:
    """
    🔧 Compliance Tool: Stark Law and regulatory compliance information
    
    This tool provides compliance-related information including:
    - Stark Law spending limits and current status
    - Risk assessments and recommendations
    - Compliance monitoring and alerts
    
    Args:
        doctor_name: Name of the healthcare professional
        
    Returns:
        str: Formatted compliance information and recommendations
    """
    print(f"🔧 Compliance Tool Called: doctor={doctor_name}")
    
    compliance_info = salesforce_data.get_compliance_info(doctor_name)
    
    if not compliance_info:
        return f"No compliance data available for {doctor_name}"
    
    compliance = compliance_info[0]  # Get first (should be only) result
    
    result = f"**Stark Law Compliance - {compliance['doctor']}:**\n\n"
    result += f"• Annual Limit: ${compliance['annual_limit']:,}\n"
    result += f"• Current Spent: ${compliance['current_spent']:,}\n"
    result += f"• Remaining Budget: ${compliance['remaining']:,}\n"
    result += f"• Utilization: {compliance['percentage_used']:.1f}%\n"
    result += f"• Risk Level: {compliance['risk_level']}\n"
    result += f"• Last Updated: {compliance['last_updated']}\n\n"
    
    # Add recommendations based on risk level
    if compliance['risk_level'] == "High":
        result += "⚠️ **Recommendations:**\n"
        result += "• Monitor spending closely\n"
        result += "• Consider alternative engagement strategies\n"
        result += "• Consult compliance team before additional activities\n"
    elif compliance['risk_level'] == "Medium":
        result += "📊 **Recommendations:**\n"
        result += "• Regular monitoring recommended\n"
        result += "• Plan remaining activities carefully\n"
    else:
        result += "✅ **Status:**\n"
        result += "• Compliance status is healthy\n"
        result += "• Continue with planned activities\n"
    
    return result

# Export all tools for easy importing
__all__ = [
    'query_salesforce_tool',
    'query_veeva_tool', 
    'query_knowledge_tool',
    'query_tableau_tool',
    'query_compliance_tool',
    'SalesContext',
    'OrderInfo',
    'EngagementInfo',
    'KnowledgeResult'
]