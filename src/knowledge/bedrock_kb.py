"""
AWS Bedrock Knowledge Base Integration
Provides access to product information, training materials, and documentation
"""

import boto3
import os
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError, NoCredentialsError

class BedrockKnowledgeBase:
    """AWS Bedrock Knowledge Base integration for product information"""
    
    def __init__(
        self,
        knowledge_base_id: Optional[str] = None,
        model_arn: Optional[str] = None,
        region_name: Optional[str] = None
    ):
        """
        Initialize Bedrock Knowledge Base client
        
        Args:
            knowledge_base_id: AWS Knowledge Base ID
            model_arn: ARN of the model to use for retrieval
            region_name: AWS region name
        """
        self.knowledge_base_id = knowledge_base_id or os.getenv(
            "BEDROCK_KNOWLEDGE_BASE_ID", 
            "WYAHSIZEAR"
        )
        self.model_arn = model_arn or os.getenv(
            "BEDROCK_MODEL_ARN",
            "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-v2"
        )
        self.region_name = region_name or os.getenv("AWS_REGION_NAME", "us-west-2")
        
        self.client = None
        self.available = False
        
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the Bedrock client and test connection"""
        try:
            self.client = boto3.client(
                'bedrock-agent-runtime',
                region_name=self.region_name
            )
            
            # Test connection with a simple query
            self._test_connection()
            self.available = True
            print("✅ Bedrock Knowledge Base initialized successfully")
            
        except NoCredentialsError:
            print("⚠️ AWS credentials not configured. Knowledge Base will use mock responses.")
            self.available = False
            
        except ClientError as e:
            print(f"⚠️ AWS Bedrock client error: {e}. Knowledge Base will use mock responses.")
            self.available = False
            
        except Exception as e:
            print(f"⚠️ Failed to initialize Knowledge Base: {e}. Using mock responses.")
            self.available = False
    
    def _test_connection(self) -> None:
        """Test the Knowledge Base connection with a simple query"""
        if not self.client:
            raise Exception("Bedrock client not initialized")
        
        test_response = self.client.retrieve_and_generate(
            input={'text': "What is sales training?"},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': self.knowledge_base_id,
                    'modelArn': self.model_arn,
                }
            }
        )
        
        if not test_response.get('output', {}).get('text'):
            raise Exception("Invalid response from Knowledge Base")
        
        print("🧪 Knowledge Base connection test successful")
    
    def query(self, query: str) -> str:
        """
        Query the Knowledge Base
        
        Args:
            query: The question or topic to search for
            
        Returns:
            Response text from the Knowledge Base
        """
        if not self.available or not self.client:
            return self._get_mock_response(query)
        
        try:
            response = self.client.retrieve_and_generate(
                input={'text': query},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': self.knowledge_base_id,
                        'modelArn': self.model_arn,
                    }
                }
            )
            
            return response['output']['text']
            
        except Exception as e:
            print(f"❌ Knowledge Base query failed: {e}")
            return self._get_mock_response(query)
    
    def _get_mock_response(self, query: str) -> str:
        """Generate mock responses when Knowledge Base is not available"""
        query_lower = query.lower()
        
        # Product-specific responses
        if "guardant360" in query_lower:
            return """
            **Guardant360 Overview:**
            
            Guardant360 is a comprehensive genomic profiling test for advanced cancer patients. 
            
            **Key Features:**
            • Comprehensive genomic profiling of 74+ genes
            • Liquid biopsy technology using blood samples
            • 7-9 day turnaround time
            • Identifies actionable mutations and therapy options
            • Non-invasive alternative to tissue biopsy
            
            **Clinical Benefits:**
            • Guides targeted therapy selection
            • Monitors treatment response
            • Detects resistance mutations
            • Supports clinical trial matching
            """
        
        elif "guardant reveal" in query_lower or "reveal" in query_lower:
            return """
            **Guardant Reveal Overview:**
            
            Guardant Reveal is a blood-based colorectal cancer screening test.
            
            **Key Features:**
            • Early detection of colorectal cancer
            • Simple blood draw procedure
            • High sensitivity and specificity
            • Complements existing screening methods
            
            **Clinical Benefits:**
            • Non-invasive screening option
            • Increases patient compliance
            • Early stage detection capability
            """
        
        elif "guardantomni" in query_lower or "omni" in query_lower:
            return """
            **GuardantOMNI Overview:**
            
            GuardantOMNI is a comprehensive 500+ gene panel for research applications.
            
            **Key Features:**
            • Largest gene panel available
            • Research-grade comprehensive profiling
            • Supports biomarker discovery
            • Enables research collaboration
            """
        
        elif any(word in query_lower for word in ["sales", "training", "process"]):
            return f"""
            **Sales Training Materials:**
            
            Training resources and best practices for '{query}' are available in our comprehensive sales training database.
            
            **Topics Covered:**
            • Product knowledge and specifications
            • Clinical evidence and studies
            • Competitive positioning
            • Customer objection handling
            • Compliance and regulatory requirements
            
            **Additional Resources:**
            • Interactive training modules
            • Case studies and success stories
            • Sales playbooks and scripts
            • Clinical utility presentations
            """
        
        else:
            return f"""
            **Knowledge Base Response:**
            
            Information about '{query}' is available in our training materials and product documentation database.
            
            **Available Resources:**
            • Product specifications and features
            • Clinical studies and evidence
            • Training materials and guidelines
            • Best practices and case studies
            • Regulatory and compliance information
            
            For specific details, please refer to the complete training materials in the sales knowledge base.
            """
    
    def get_product_info(self, product_name: str) -> str:
        """Get specific product information"""
        return self.query(f"Tell me about {product_name} features and benefits")
    
    def get_training_material(self, topic: str) -> str:
        """Get training material for a specific topic"""
        return self.query(f"Training materials for {topic}")
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health status of the Knowledge Base connection"""
        return {
            "available": self.available,
            "knowledge_base_id": self.knowledge_base_id,
            "region": self.region_name,
            "client_initialized": self.client is not None
        }

# Global instance for easy import
knowledge_base = BedrockKnowledgeBase()