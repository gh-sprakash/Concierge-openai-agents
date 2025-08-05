"""
Salesforce Data Source - Mock data for sales orders and compliance
Simulates Salesforce CRM data with realistic business information
"""

from typing import Dict, List, Any
from datetime import datetime, timedelta
import random

class SalesforceDataSource:
    """Salesforce CRM data source with order and compliance information"""
    
    def __init__(self):
        self.data = self._generate_mock_data()
    
    def _generate_mock_data(self) -> Dict[str, Any]:
        """Generate realistic mock Salesforce data"""
        # Generate dates for the last 30 days
        base_date = datetime(2024, 1, 1)
        
        orders = [
            {
                "doctor": "Dr. Sarah Johnson",
                "order_id": "ORD-001",
                "status": "On Hold",
                "product": "Guardant360",
                "date": "2024-01-15",
                "amount": 2500,
                "quantity": 1,
                "hospital": "General Hospital",
                "specialty": "Oncology"
            },
            {
                "doctor": "Dr. Julie Martinez",
                "order_id": "ORD-012",
                "status": "On Hold", 
                "product": "Guardant360",
                "date": "2024-01-21",
                "amount": 2500,
                "quantity": 1,
                "hospital": "Health System North",
                "specialty": "Oncology"
            },
            {
                "doctor": "Dr. Julie Martinez",
                "order_id": "ORD-013",
                "status": "Completed",
                "product": "Guardant Reveal",
                "date": "2024-01-18",
                "amount": 3600,
                "quantity": 2,
                "hospital": "Health System North", 
                "specialty": "Oncology"
            },
            {
                "doctor": "Dr. Ahmed Shafique",
                "order_id": "ORD-009",
                "status": "Completed",
                "product": "Guardant360",
                "date": "2024-01-20",
                "amount": 2500,
                "quantity": 1,
                "hospital": "Regional Medical Center",
                "specialty": "Pathology"
            },
            {
                "doctor": "Dr. Ahmed Shafique",
                "order_id": "ORD-014",
                "status": "Processing",
                "product": "GuardantOMNI",
                "date": "2024-01-25",
                "amount": 4200,
                "quantity": 1,
                "hospital": "Regional Medical Center",
                "specialty": "Pathology"
            }
        ]
        
        # Stark Law compliance data
        stark_compliance = [
            {
                "doctor": "Dr. Ahmed Shafique",
                "annual_limit": 5000,
                "current_spent": 3250,
                "remaining": 1750,
                "risk_level": "Medium",
                "percentage_used": 65.0,
                "last_updated": "2024-01-25"
            },
            {
                "doctor": "Dr. Julie Martinez", 
                "annual_limit": 3500,
                "current_spent": 2100,
                "remaining": 1400,
                "risk_level": "Low",
                "percentage_used": 60.0,
                "last_updated": "2024-01-25"
            },
            {
                "doctor": "Dr. Sarah Johnson",
                "annual_limit": 6000,
                "current_spent": 4200,
                "remaining": 1800,
                "risk_level": "High", 
                "percentage_used": 70.0,
                "last_updated": "2024-01-25"
            }
        ]
        
        return {
            "orders": orders,
            "stark_compliance": stark_compliance
        }
    
    def get_doctor_orders(self, doctor_name: str = None) -> List[Dict[str, Any]]:
        """Get orders for a specific doctor or all doctors"""
        if doctor_name:
            return [
                order for order in self.data["orders"]
                if doctor_name.lower() in order["doctor"].lower()
            ]
        return self.data["orders"]
    
    def get_compliance_info(self, doctor_name: str = None) -> List[Dict[str, Any]]:
        """Get Stark Law compliance information"""
        if doctor_name:
            return [
                compliance for compliance in self.data["stark_compliance"]
                if doctor_name.lower() in compliance["doctor"].lower()
            ]
        return self.data["stark_compliance"]
    
    def get_order_summary(self, doctor_name: str = None) -> Dict[str, Any]:
        """Get order summary statistics"""
        orders = self.get_doctor_orders(doctor_name)
        
        total_orders = len(orders)
        total_value = sum(order["amount"] for order in orders)
        
        # Status breakdown
        status_summary = {}
        for order in orders:
            status = order["status"]
            status_summary[status] = status_summary.get(status, 0) + 1
        
        # Recent orders (last 3)
        recent_orders = sorted(orders, key=lambda x: x["date"])[-3:]
        
        return {
            "doctor": doctor_name or "All Doctors",
            "total_orders": total_orders,
            "total_value": total_value,
            "status_summary": status_summary,
            "recent_orders": recent_orders
        }

# Global instance for easy import
salesforce_data = SalesforceDataSource()