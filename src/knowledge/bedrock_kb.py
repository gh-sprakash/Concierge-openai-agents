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
        
        # Use retrieve method for testing instead of retrieve_and_generate
        test_response = self.client.retrieve(
            knowledgeBaseId=self.knowledge_base_id,
            retrievalQuery={'text': "What is sales training?"},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 1
                }
            }
        )
        
        if not test_response.get('retrievalResults'):
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

    def retrieve_documents(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Retrieve relevant document chunks from the Knowledge Base without generation.
        
        Args:
            query: The question or topic to search for
            max_results: Maximum number of document chunks to retrieve
            
        Returns:
            Dict containing retrieved document chunks and sources
        """
        # Fallback to mock if KB is unavailable
        if not self.available or not self.client:
            return {
                "chunks": [self._get_mock_response(query)],
                "sources": self._get_mock_sources(query)
            }

        try:
            response = self.client.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results
                    }
                }
            )

            # Extract document chunks and sources from retrieve response
            chunks = []
            sources = []
            
            retrieval_results = response.get('retrievalResults', [])
            for result in retrieval_results:
                # Extract content text
                content = result.get('content', {})
                if isinstance(content, dict):
                    text = content.get('text', '')
                else:
                    text = str(content)
                
                if text:
                    chunks.append(text)
                
                # Extract source information
                source = {}
                location = result.get('location', {})
                
                # Handle different location types
                if 's3Location' in location:
                    s3 = location['s3Location']
                    bucket = s3.get('bucket')
                    key = s3.get('key')
                    source['uri'] = f"s3://{bucket}/{key}" if bucket and key else None
                elif 'url' in location:
                    source['uri'] = location.get('url')
                
                # Add snippet and metadata
                source['snippet'] = text[:200] + "..." if len(text) > 200 else text
                source['title'] = result.get('metadata', {}).get('title', 'Knowledge Base Document')
                
                # Add score if available
                score = result.get('score')
                if score is not None:
                    source['relevance_score'] = score
                
                # Add metadata
                metadata = result.get('metadata', {})
                if metadata:
                    source['metadata'] = metadata
                
                # Clean Nones and add if not empty
                source = {k: v for k, v in source.items() if v is not None}
                if source:
                    sources.append(source)

            return {
                "chunks": chunks,
                "sources": sources
            }

        except Exception as e:
            print(f"❌ Knowledge Base retrieve_documents failed: {e}")
            return {
                "chunks": [self._get_mock_response(query)],
                "sources": self._get_mock_sources(query)
            }

    def query_with_sources(self, query: str) -> Dict[str, Any]:
        """
        Legacy method that now uses retrieve_documents instead of retrieve_and_generate.
        Returns document chunks joined as text for backward compatibility.

        Returns a dict: { 'text': str, 'sources': List[Dict[str, Any]] }
        """
        result = self.retrieve_documents(query)
        
        # Join chunks into a single text response for compatibility
        chunks = result.get('chunks', [])
        combined_text = "\n\n".join(chunks) if chunks else ""
        
        return {
            "text": combined_text,
            "sources": result.get('sources', [])
        }

    def _extract_sources(self, response: Dict[str, Any]):
        """Best-effort extraction of source documents from Bedrock RnG response."""
        sources: list[Dict[str, Any]] = []
        try:
            citations = response.get('citations') or []
            for citation in citations:
                refs = citation.get('retrievedReferences') or []
                for ref in refs:
                    source: Dict[str, Any] = {}
                    # Location info (varies by connector)
                    location = ref.get('location') or {}
                    if 's3Location' in location:
                        s3 = location['s3Location']
                        bucket = s3.get('bucket')
                        key = s3.get('key')
                        source['uri'] = f"s3://{bucket}/{key}" if bucket and key else None
                    elif 'kendraDocumentId' in location:
                        source['kendraDocumentId'] = location.get('kendraDocumentId')
                    elif 'url' in location:
                        source['uri'] = location.get('url')

                    # Content/snippet if present
                    content = ref.get('content')
                    if isinstance(content, dict):
                        # Newer payloads may use text within a dict
                        source['snippet'] = content.get('text') or content.get('body')
                        source['title'] = content.get('title')
                    elif isinstance(content, str):
                        source['snippet'] = content

                    # Metadata
                    metadata = ref.get('metadata') or {}
                    if metadata:
                        source['metadata'] = metadata

                    # Clean Nones
                    source = {k: v for k, v in source.items() if v is not None}
                    if source:
                        sources.append(source)

        except Exception as e:
            print(f"⚠️ Failed to extract sources: {e}")
        return sources

    def _get_mock_sources(self, query: str):
        """Provide mock source documents for local/dev usage."""
        return [
            {
                "title": "Mock KB: Product Overview",
                "uri": "s3://mock-bucket/knowledge/product-overview.md",
                "snippet": f"Auto-generated reference for '{query}' (overview)",
            },
            {
                "title": "Mock KB: Clinical Study Summary",
                "uri": "s3://mock-bucket/knowledge/clinical-study.pdf",
                "snippet": f"Auto-generated reference for '{query}' (clinical)",
            },
        ]
        
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