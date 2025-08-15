import boto3
import json
import os
import logging
from pydantic import BaseModel, Field
from typing import Optional
import openai

class ExtractedMetadata(BaseModel):
    """Metadata extracted by LLM from file content"""
    content_date: Optional[str] = Field(default=None, description="Document date in YYYY-MM format")
    content_type: str = Field(description="Content type: Product Information, Process Training, Competitor Analysis, or Other")
    country_region: Optional[str] = Field(default=None, description="Regional focus if specific: US, EU, APAC, LATAM, Other")
    area: Optional[str] = Field(default=None, description="US region if specific: West, Northeast, Southeast")


async def process_file_metadata(
    bucket_name: str,
    object_key: str, 
    existing_metadata: dict, 
    s3_client: boto3.client = None,
    model: str = "gpt-4o",
    logger: logging.Logger = None
) -> dict:
    """
    Complete metadata processing pipeline for S3 files.
    
    Downloads file from S3, extracts metadata using LLM, and saves metadata back to S3.
    Supports PDF, DOCX, and Excel files without parsing.
    
    Args:
        bucket_name: S3 bucket name
        object_key: S3 object key (path to file)
        existing_metadata: Existing metadata for the file
        s3_client: Boto3 S3 client (creates default if None)
        model: Model to use for extraction (default: gpt-4o)
        logger: Logger instance for logging (creates default if None)
        
    Returns:
        dict: Extracted metadata that was saved to S3
        
    Example:
        >>> import logging
        >>> logger = logging.getLogger(__name__)
        >>> s3 = boto3.client('s3')
        >>> metadata = await process_file_metadata(
        ...     "my-bucket", 
        ...     "docs/product-guide.pdf", 
        ...     existing_metadata,
        ...     s3,
        ...     logger=logger
        ... )
        >>> print(metadata['content_type'])  # "Product Information"
    """
    if s3_client is None:
        s3_client = boto3.client('s3')
    
    if logger is None:
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
    
    logger.info(f"Starting metadata processing for {object_key}")
    
    try:
        # Download file from S3
        logger.debug(f"Downloading file from S3: {bucket_name}/{object_key}")
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        file_content = response['Body'].read()
        logger.info(f"Downloaded file: {len(file_content):,} bytes")
        
        # Use OpenAI Chat Completions API with a simple text-based approach
        client = openai.OpenAI()
        
        # Get file type for analysis
        file_type = os.path.splitext(object_key)[1].lower()
        logger.debug(f"File type detected: {file_type}")
        
        logger.info(f"Extracting metadata using {model}")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": """You are a document metadata extractor. Analyze the document information provided and extract metadata.

Return ONLY a valid JSON object with these exact fields:
{
  "content_date": "YYYY-MM or null",
  "content_type": "Product Information or Process Training or Competitor Analysis or Other",
  "country_region": "US or EU or APAC or LATAM or Other or null",
  "area": "West or Northeast or Southeast or null"
}

Rules:
- content_date: Extract date in YYYY-MM format, return null if not found
- content_type: Choose the most appropriate category
- country_region: Only if document is region-specific, otherwise null
- area: Only if document is US region-specific, otherwise null
- Be conservative with regional assignments"""
                },
                {
                    "role": "user",
                    "content": f"""Extract metadata from this document:

File: {object_key}
Type: {file_type}
Size: {len(file_content):,} bytes

Analyze the filename to determine:
- Content type (look for keywords like "training", "product", "competitor", etc.)
- Date information (look for dates, version numbers)
- Regional information (look for country/region codes, area names)

Based on the filename "{object_key}" and file type "{file_type}", extract the metadata."""
                }
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        # Parse response
        try:
            response_text = response.choices[0].message.content.strip()
            metadata_json = json.loads(response_text)
            llm_metadata = ExtractedMetadata(**metadata_json)
            logger.debug(f"Successfully extracted metadata: {metadata_json}")
        except Exception as parse_error:
            logger.error(f"Error parsing LLM response: {parse_error}")
            logger.debug(f"Raw response: {response.choices[0].message.content}")
            # Use defaults
            llm_metadata = ExtractedMetadata(
                content_date=None,
                content_type="Other",
                country_region=None,
                area=None
            )
        
        # Build final metadata with defaults
        metadata = {
            "department": existing_metadata.get("department", "Sales & Marketing"),
            "content_date": llm_metadata.content_date or existing_metadata.get("content_date", ""),
            "content_type": llm_metadata.content_type or existing_metadata.get("content_type", ""),
            "country_region": llm_metadata.country_region or existing_metadata.get("country_region", "US"),
            "area": llm_metadata.area or existing_metadata.get("area", "Not Applicable"),
            "is_personal_file": "false"
        }
        
        # Save metadata to S3
        metadata_key = f"{object_key}.metadata.json"
        response = s3_client.put_object(
            Bucket=bucket_name, 
            Key=metadata_key, 
            Body=json.dumps(metadata, indent=2)
        )
        # Check if the object was saved successfully
        if response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
            logger.info(f"Metadata successfully saved to S3 as {metadata_key}")
        else:
            logger.error(f"Failed to save metadata to S3 for {metadata_key}")
        
        logger.info(f"Completed metadata processing for {object_key}")
        return metadata
        
    except Exception as e:
        # Return defaults on error
        logger.error(f"Error processing {object_key}: {e}")
        default_metadata = {
            "department": existing_metadata.get("department", "Sales & Marketing"),
            "content_date": existing_metadata.get("content_date", ""),
            "content_type": existing_metadata.get("content_type", "Other"),
            "country_region": existing_metadata.get("country_region", "US"), 
            "area": existing_metadata.get("area", "Not Applicable"),
            "is_personal_file": "false"
        }
        
        # Still save defaults to S3
        try:
            object_name = object_key.split("/")[-1]
            metadata_key = f"{object_name}.metadata.json"
            s3_client.put_object(
                Bucket=bucket_name,
                Key=metadata_key,
                Body=json.dumps(default_metadata, indent=2)
            )
        except:
            pass
            
        return default_metadata


# Example usage
# if __name__ == "__main__":
#     import asyncio
    
#     async def example():
#         # Setup custom logger
#         logger = logging.getLogger("metadata_processor")
#         logger.setLevel(logging.DEBUG)
        
#         metadata = await process_file_metadata(
#             bucket_name="consiergeai-salesrep-training",
#             object_key="salesrep/[GUAR514] Tumor One-Pagers - Breast R8.00 CMYK.pdf", 
#             existing_metadata={
#                 "department": "Sales & Marketing"
#             },
#             logger=logger
#         )
#         print("Processed metadata:", metadata)
    
#     asyncio.run(example())