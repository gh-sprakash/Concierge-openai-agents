"""
Tableau Analytics Data Source - Business intelligence and performance metrics
Provides insights into test ordering trends and business analytics
"""

from typing import Dict, List, Any
from datetime import datetime, timedelta
import random

class TableauDataSource:
    """Tableau analytics data source for business intelligence"""
    
    def __init__(self):
        self.data = self._generate_mock_data()
    
    def _generate_mock_data(self) -> Dict[str, Any]:
        """Generate realistic mock analytics data"""
        
        # Test ordering trends for different products
        test_ordering_trends = [
            {
                "product": "Guardant360",
                "month": "2024-01",
                "orders": 47,
                "completed": 44,
                "cancelled": 3,
                "growth": "+4.4%",
                "completion_rate": 93.6,
                "avg_turnaround_days": 7.2
            },
            {
                "product": "GuardantOMNI",
                "month": "2024-01", 
                "orders": 33,
                "completed": 30,
                "cancelled": 3,
                "growth": "+5.4%",
                "completion_rate": 90.9,
                "avg_turnaround_days": 10.1
            },
            {
                "product": "Guardant Reveal",
                "month": "2024-01",
                "orders": 31,
                "completed": 29,
                "cancelled": 2,
                "growth": "+20.6%", 
                "completion_rate": 93.5,
                "avg_turnaround_days": 8.5
            }
        ]
        
        # Regional performance data
        regional_performance = [
            {
                "region": "Northeast",
                "total_orders": 156,
                "revenue": 425000,
                "growth": "+8.2%",
                "top_products": ["Guardant360", "Guardant Reveal"],
                "key_accounts": 23
            },
            {
                "region": "Southeast", 
                "total_orders": 203,
                "revenue": 567000,
                "growth": "+12.1%",
                "top_products": ["GuardantOMNI", "Guardant360"],
                "key_accounts": 31
            },
            {
                "region": "West",
                "total_orders": 134,
                "revenue": 378000,
                "growth": "+6.7%",
                "top_products": ["Guardant360", "Guardant Reveal"],
                "key_accounts": 19
            }
        ]
        
        # Customer satisfaction metrics
        satisfaction_metrics = {
            "overall_satisfaction": 4.2,
            "turnaround_time_satisfaction": 4.0,
            "support_quality": 4.5,
            "product_quality": 4.6,
            "total_responses": 89,
            "nps_score": 67
        }
        
        return {
            "test_ordering_trends": test_ordering_trends,
            "regional_performance": regional_performance,
            "satisfaction_metrics": satisfaction_metrics
        }
    
    def get_product_trends(self, product_name: str = None) -> List[Dict[str, Any]]:
        """Get test ordering trends for specific product or all products"""
        trends = self.data["test_ordering_trends"]
        if product_name:
            return [
                trend for trend in trends
                if product_name.lower() in trend["product"].lower()
            ]
        return trends
    
    def get_regional_performance(self, region: str = None) -> List[Dict[str, Any]]:
        """Get regional performance data"""
        performance = self.data["regional_performance"]
        if region:
            return [
                perf for perf in performance
                if region.lower() in perf["region"].lower()
            ]
        return performance
    
    def get_analytics_summary(self) -> str:
        """Get formatted analytics summary"""
        trends = self.data["test_ordering_trends"]
        
        summary = "📊 Test Ordering Trends (January 2024):\n\n"
        
        for trend in trends:
            summary += (
                f"• {trend['product']}: {trend['orders']} orders "
                f"({trend['growth']} growth, {trend['completion_rate']}% completion, "
                f"{trend['avg_turnaround_days']} days avg turnaround)\n"
            )
        
        # Add regional summary
        regions = self.data["regional_performance"]
        total_orders = sum(region["total_orders"] for region in regions)
        total_revenue = sum(region["revenue"] for region in regions)
        
        summary += f"\n📍 Regional Summary:\n"
        summary += f"• Total Orders: {total_orders:,}\n"
        summary += f"• Total Revenue: ${total_revenue:,}\n"
        
        # Add satisfaction metrics
        sat = self.data["satisfaction_metrics"]
        summary += f"\n⭐ Customer Satisfaction:\n"
        summary += f"• Overall: {sat['overall_satisfaction']}/5.0\n"
        summary += f"• NPS Score: {sat['nps_score']}\n"
        
        return summary
    
    def get_performance_insights(self) -> List[str]:
        """Get actionable performance insights"""
        trends = self.data["test_ordering_trends"]
        regions = self.data["regional_performance"]
        
        insights = []
        
        # Product performance insights
        best_growth = max(trends, key=lambda x: float(x["growth"].replace("%", "").replace("+", "")))
        insights.append(f"🚀 {best_growth['product']} shows strongest growth at {best_growth['growth']}")
        
        best_completion = max(trends, key=lambda x: x["completion_rate"])
        insights.append(f"✅ {best_completion['product']} has highest completion rate at {best_completion['completion_rate']}%")
        
        # Regional insights
        best_region = max(regions, key=lambda x: x["revenue"])
        insights.append(f"💰 {best_region['region']} leads in revenue with ${best_region['revenue']:,}")
        
        return insights

# Global instance for easy import
tableau_data = TableauDataSource()