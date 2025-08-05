"""
Veeva CRM Data Source - Healthcare professional engagement data
Tracks interactions, meetings, and relationship building activities
"""

from typing import Dict, List, Any
from datetime import datetime

class VeevaDataSource:
    """Veeva CRM data source for healthcare professional engagements"""
    
    def __init__(self):
        self.data = self._generate_mock_data()
    
    def _generate_mock_data(self) -> Dict[str, Any]:
        """Generate realistic mock Veeva engagement data"""
        engagements = [
            {
                "doctor": "Dr. Julie Martinez",
                "engagement_id": "ENG-012",
                "type": "Email Communication",
                "date": "2024-01-22",
                "rep": "Maria Garcia",
                "outcome": "Positive - Questions answered",
                "talking_points": [
                    "Technical specifications clarified",
                    "Ordering process simplified", 
                    "Support availability confirmed"
                ],
                "next_steps": "Follow up in 2 weeks for ordering decision",
                "contacts_made": [
                    {
                        "contact_type": "phone_call",
                        "contact": "Lab Director John Smith",
                        "date": "2024-01-20",
                        "purpose": "Test logistics discussion"
                    },
                    {
                        "contact_type": "email",
                        "contact": "Pathologist Dr. Williams", 
                        "date": "2024-01-21",
                        "purpose": "Result interpretation guidance"
                    },
                    {
                        "contact_type": "meeting",
                        "contact": "Hospital Administrator Ms. Davis",
                        "date": "2024-01-22", 
                        "purpose": "Budget and procurement discussion"
                    }
                ]
            },
            {
                "doctor": "Dr. Ahmed Shafique",
                "engagement_id": "ENG-013", 
                "type": "In-Person Visit",
                "date": "2024-01-20",
                "rep": "John Smith",
                "outcome": "Positive - Discussed volume pricing",
                "talking_points": [
                    "Volume discounts available for bulk orders",
                    "Streamlined bulk ordering process",
                    "Dedicated implementation support"
                ],
                "next_steps": "Prepare volume pricing proposal",
                "contacts_made": [
                    {
                        "contact_type": "meeting",
                        "contact": "Hospital Administrator Jane Doe",
                        "date": "2024-01-19",
                        "purpose": "Budget approval process"
                    },
                    {
                        "contact_type": "phone_call", 
                        "contact": "IT Manager Bob Johnson",
                        "date": "2024-01-20",
                        "purpose": "System integration requirements"
                    },
                    {
                        "contact_type": "email",
                        "contact": "Procurement Director Lisa Wang",
                        "date": "2024-01-20",
                        "purpose": "Contract terms negotiation"
                    }
                ]
            },
            {
                "doctor": "Dr. Sarah Johnson",
                "engagement_id": "ENG-001",
                "type": "In-Person Visit", 
                "date": "2024-01-15",
                "rep": "John Smith",
                "outcome": "Positive - Interested in Guardant360",
                "talking_points": [
                    "Guardant360 comprehensive genomic profiling",
                    "Faster turnaround time benefits",
                    "Clinical utility and impact on patient care"
                ],
                "next_steps": "Schedule product demonstration",
                "contacts_made": [
                    {
                        "contact_type": "email",
                        "contact": "Oncology Nurse Lisa Chen",
                        "date": "2024-01-14", 
                        "purpose": "Workflow integration discussion"
                    },
                    {
                        "contact_type": "phone_call",
                        "contact": "Medical Director Dr. Brown",
                        "date": "2024-01-15",
                        "purpose": "Clinical approval and adoption"
                    }
                ]
            }
        ]
        
        return {"engagements": engagements}
    
    def get_doctor_engagements(self, doctor_name: str) -> List[Dict[str, Any]]:
        """Get all engagements for a specific doctor"""
        return [
            eng for eng in self.data["engagements"]
            if doctor_name.lower() in eng["doctor"].lower()
        ]
    
    def get_latest_engagement(self, doctor_name: str) -> Dict[str, Any]:
        """Get the most recent engagement for a doctor"""
        engagements = self.get_doctor_engagements(doctor_name)
        if not engagements:
            return {
                "doctor": doctor_name,
                "last_engagement_date": "No data",
                "engagement_type": "No data", 
                "outcome": "No data",
                "talking_points": ["No engagement data available"],
                "contacts_made": []
            }
        
        # Sort by date and get the latest
        latest = sorted(engagements, key=lambda x: x["date"])[-1]
        return {
            "doctor": doctor_name,
            "last_engagement_date": latest["date"],
            "engagement_type": latest["type"],
            "outcome": latest["outcome"],
            "talking_points": latest["talking_points"],
            "contacts_made": latest["contacts_made"]
        }
    
    def get_engagement_summary(self) -> Dict[str, Any]:
        """Get overall engagement summary statistics"""
        engagements = self.data["engagements"]
        
        total_engagements = len(engagements)
        
        # Engagement types breakdown
        types_summary = {}
        for eng in engagements:
            eng_type = eng["type"]
            types_summary[eng_type] = types_summary.get(eng_type, 0) + 1
        
        # Outcomes summary
        outcomes_summary = {}
        for eng in engagements:
            outcome = eng["outcome"].split(" - ")[0]  # Get just "Positive/Negative"
            outcomes_summary[outcome] = outcomes_summary.get(outcome, 0) + 1
        
        return {
            "total_engagements": total_engagements,
            "types_summary": types_summary,
            "outcomes_summary": outcomes_summary
        }

# Global instance for easy import
veeva_data = VeevaDataSource()