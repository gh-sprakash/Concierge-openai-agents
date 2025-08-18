import boto3
import json
import os
import logging
import tempfile
from pathlib import Path
from typing import Optional, List
from io import BytesIO

from pydantic import BaseModel, Field
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser


class ExtractedMetadata(BaseModel):
    """Metadata extracted by LLM from file content"""
    content_date: Optional[str] = Field(default=None, description="Document date in YYYY-MM format")
    content_type: str = Field(description="Content type: Product Information, Process Training, Competitor Analysis, or Other")
    country_region: Optional[str] = Field(default=None, description="Regional focus if specific: US, EU, APAC, LATAM, Other")
    area: Optional[str] = Field(default=None, description="US region if specific: West, Northeast, Southeast")


def setup_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a standardized logger for the metadata processing pipeline.
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only add handler if one doesn't exist to avoid duplicates
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    
    return logger


def get_default_metadata(existing_metadata: dict) -> dict:
    """
    Get default metadata structure with fallback values.
    
    Args:
        existing_metadata: Existing metadata to merge with defaults
        
    Returns:
        Complete metadata dictionary with defaults
    """
    return {
        "department": existing_metadata.get("department", "Sales & Marketing"),
        "content_date": existing_metadata.get("content_date", None),
        "content_type": existing_metadata.get("content_type", "Other"),
        "country_region": existing_metadata.get("country_region", None),
        "area": existing_metadata.get("area", None),
        "is_personal_file": existing_metadata.get("is_personal_file", "false"),
        "version": existing_metadata.get("version", "Final")
    }


def download_file_from_s3(bucket_name: str, object_key: str, s3_client: boto3.client, logger: logging.Logger) -> bytes:
    """
    Download a file from S3.
    
    Args:
        bucket_name: S3 bucket name
        object_key: S3 object key
        s3_client: Boto3 S3 client
        logger: Logger instance
        
    Returns:
        File content as bytes
        
    Raises:
        Exception: If download fails
    """
    logger.info(f"Downloading file from S3: s3://{bucket_name}/{object_key}")
    
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        file_content = response['Body'].read()
        file_size_mb = len(file_content) / (1024 * 1024)
        
        logger.info(f"Successfully downloaded file: {len(file_content):,} bytes ({file_size_mb:.2f} MB)")
        return file_content
        
    except Exception as e:
        logger.error(f"Failed to download file from S3: {e}")
        raise


def get_file_extension(filename: str) -> str:
    """Get the file extension from filename."""
    return Path(filename).suffix.lower()


def extract_text_with_langchain(file_content: bytes, filename: str, logger: logging.Logger) -> str:
    """
    Extract text from file using appropriate LangChain document loader.
    
    Args:
        file_content: File content as bytes
        filename: Original filename for extension detection
        logger: Logger instance
        
    Returns:
        Extracted text content
        
    Raises:
        Exception: If text extraction fails
    """
    file_extension = get_file_extension(filename)
    logger.info(f"Extracting text from {file_extension} file: {filename}")
    
    try:
        # Create a temporary file for the document loader
        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            documents = []
            
            if file_extension == '.pdf':
                logger.debug("Using PyPDFLoader for PDF extraction")
                loader = PyPDFLoader(temp_file_path)
                documents = loader.load()
                
            elif file_extension in ['.docx', '.doc']:
                logger.debug("Using Docx2txtLoader for Word document extraction")
                loader = Docx2txtLoader(temp_file_path)
                documents = loader.load()
                
            elif file_extension in ['.xlsx', '.xls']:
                # For Excel files, we'll use a simple approach since LangChain doesn't have a dedicated loader
                logger.debug("Processing Excel file - extracting sheet names and basic info")
                try:
                    import openpyxl
                    from openpyxl import load_workbook
                    
                    workbook = load_workbook(temp_file_path, read_only=True)
                    sheet_info = []
                    
                    for sheet_name in workbook.sheetnames:
                        sheet = workbook[sheet_name]
                        # Get first few rows to understand content
                        content_preview = []
                        for row_num, row in enumerate(sheet.iter_rows(max_row=10, values_only=True)):
                            if any(cell for cell in row if cell is not None):
                                content_preview.append(' '.join(str(cell) for cell in row if cell is not None))
                        
                        sheet_info.append(f"Sheet '{sheet_name}': {'; '.join(content_preview[:3])}")
                    
                    text_content = f"Excel workbook with sheets: {'; '.join(sheet_info)}"
                    
                except Exception as e:
                    logger.warning(f"Failed to extract Excel content: {e}")
                    text_content = f"Excel file: {filename} (unable to extract detailed content)"
                
                # Create a mock document for consistency
                from langchain_core.documents import Document
                documents = [Document(page_content=text_content, metadata={"source": filename})]
                
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            # Combine all document content
            if documents:
                text_content = "\n\n".join([doc.page_content for doc in documents])
                logger.info(f"Successfully extracted {len(text_content):,} characters from {len(documents)} document(s)")
                return text_content
            else:
                raise Exception("No content extracted from document")
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except Exception as e:
        logger.error(f"Failed to extract text from {filename}: {e}")
        raise


def extract_metadata_with_langchain(text_content: str, model: str, logger: logging.Logger) -> Optional[ExtractedMetadata]:
    """
    Extract metadata using LangChain structured output.
    
    Args:
        text_content: Extracted text content from document
        model: OpenAI model to use
        logger: Logger instance
        
    Returns:
        Extracted metadata or None if extraction failed
    """
    logger.info(f"Extracting metadata using LangChain with model: {model}")
    
    try:
        # Set up the parser
        parser = PydanticOutputParser(pydantic_object=ExtractedMetadata)
        
        # Create the prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a document metadata extractor. Analyze the provided document content and extract structured metadata.

Focus on identifying:
- Content type: Categorize as 'Product Information', 'Process Training', 'Competitor Analysis', or 'Other'
- Document date: Look for any dates mentioned in YYYY-MM format
- Geographic focus: Identify if the content focuses on specific regions (US, EU, APAC, LATAM, Other)
- US area focus: If US-focused, identify specific areas (West, Northeast, Southeast)

Be conservative - if you're not confident about a field, leave it as null/None.

{format_instructions}"""),
            ("human", "Analyze this document content:\n\n{text}")
        ])
        
        # Format the prompt with instructions
        formatted_prompt = prompt.partial(format_instructions=parser.get_format_instructions())
        
        # Initialize the LLM
        llm = ChatOpenAI(model=model, temperature=0)
        
        # Create the chain
        chain = formatted_prompt | llm | parser
        
        # Extract metadata
        logger.debug(f"Processing {len(text_content):,} characters of text content")
        metadata = chain.invoke({"text": text_content[:8000]})  # Limit to 8000 chars to avoid token limits
        
        logger.info(f"Successfully extracted metadata: content_type='{metadata.content_type}', "
                   f"content_date='{metadata.content_date}', country_region='{metadata.country_region}', "
                   f"area='{metadata.area}'")
        
        return metadata
        
    except Exception as e:
        logger.error(f"Failed to extract metadata with LangChain: {e}")
        return None


def save_metadata_to_s3(metadata: dict, bucket_name: str, object_key: str, s3_client: boto3.client, logger: logging.Logger) -> bool:
    """
    Save metadata to S3 as a JSON file.
    
    Args:
        metadata: Metadata dictionary to save
        bucket_name: S3 bucket name
        object_key: Original object key (metadata file will be named based on this)
        s3_client: Boto3 S3 client
        logger: Logger instance
        
    Returns:
        True if saved successfully, False otherwise
    """
    metadata_key = f"{object_key}.metadata.json"
    logger.info(f"Saving metadata to S3: s3://{bucket_name}/{metadata_key}")
    
    try:
        response = s3_client.put_object(
            Bucket=bucket_name,
            Key=metadata_key,
            Body=json.dumps(metadata, indent=2),
            ContentType="application/json"
        )
        
        if response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
            logger.info("Metadata successfully saved to S3")
            return True
        else:
            logger.error(f"Unexpected response from S3: {response.get('ResponseMetadata', {})}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to save metadata to S3: {e}")
        return False


async def process_file_metadata(
    bucket_name: str,
    object_key: str,
    existing_metadata: dict,
    s3_client: boto3.client = None,
    model: str = "gpt-4o",
    logger: logging.Logger = None
) -> dict:
    """
    Complete metadata processing pipeline for S3 files using LangChain.
    
    Downloads file from S3, extracts text using LangChain document loaders,
    extracts metadata using LangChain structured output, and saves metadata back to S3.
    Supports PDF, DOCX, and Excel files.
    
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
    # Initialize defaults
    if s3_client is None:
        s3_client = boto3.client('s3')
    
    if logger is None:
        logger = setup_logger()
    
    filename = os.path.basename(object_key)
    logger.info(f"Starting LangChain-based metadata processing for: {filename}")
    
    try:
        # Step 1: Download file from S3
        file_content = download_file_from_s3(bucket_name, object_key, s3_client, logger)
        
        # Step 2: Extract text using LangChain document loaders
        text_content = extract_text_with_langchain(file_content, filename, logger)
        
        # Step 3: Extract metadata using LangChain structured output
        llm_metadata = extract_metadata_with_langchain(text_content, model, logger)
        
        # Step 4: Build final metadata
        if llm_metadata:
            final_metadata = {
                "department": existing_metadata.get("department", "Sales & Marketing"),
                "content_date": existing_metadata.get("content_date", llm_metadata.content_date),
                "content_type": existing_metadata.get("content_type", llm_metadata.content_type),
                "country_region": existing_metadata.get("country_region", llm_metadata.country_region),
                "area": existing_metadata.get("area", llm_metadata.area),
                "is_personal_file": existing_metadata.get("is_personal_file", "false"),
                "version": existing_metadata.get("version", "Final")
            }
        else:
            logger.warning("Using default metadata due to LangChain extraction failure")
            final_metadata = get_default_metadata(existing_metadata)
        
        # Step 5: Save metadata to S3
        save_metadata_to_s3(final_metadata, bucket_name, object_key, s3_client, logger)
        
        logger.info(f"Successfully completed LangChain metadata processing for: {filename}")
        return final_metadata
        
    except Exception as e:
        logger.error(f"Error in LangChain metadata processing pipeline for {object_key}: {e}")
        
        # Return and save default metadata on error
        default_metadata = get_default_metadata(existing_metadata)
        
        # Attempt to save defaults to S3
        try:
            save_metadata_to_s3(default_metadata, bucket_name, object_key, s3_client, logger)
        except Exception as save_error:
            logger.error(f"Failed to save default metadata to S3: {save_error}")
        
        return default_metadata


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def example():
        # Setup logger to only print errors
        logger = setup_logger("langchain_metadata_processor", logging.INFO)
        
        metadata = await process_file_metadata(
            bucket_name="consiergeai-salesrep-training",
            object_key="salesrep/[GUAR514] Tumor One-Pagers - Breast R8.00 CMYK.pdf",
            existing_metadata={
                "department": "Sales & Marketing"
            },
            logger=logger
        )
        print("Final processed metadata:", json.dumps(metadata, indent=2))
    
    asyncio.run(example())