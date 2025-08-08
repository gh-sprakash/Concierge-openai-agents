knowledge_sources = [
    {
      "metadata": {
        "department": "MedAffairs",
        "region": "US",
        "x-amz-bedrock-kb-byte-content-source": "s3://consiergeai-salesrep-training/aws/bedrock/knowledge_bases/WYAHSIZEAR/4HILUSLBPF/6cef1c58-7495-4a71-ad31-2a64310dc017.png",
        "x-amz-bedrock-kb-data-source-id": "4HILUSLBPF",
        "x-amz-bedrock-kb-description": "<figure>\nThe Guardant360 logo, showing the word \"GUARDANT\" in grey and \"360\" in blue with a curved line underneath.\n</figure>\n# New insights now available on Guardant360\n<figure>\nA visual representation of Guardant360's features, displayed in a gradient colored banner (blue to purple to red) with information about the platform and new features available in the Guardant360 Report.\n</figure>\nGuardant360 is powered by the Guardant Infinity platform, **the only commercially available technology** that unlocks both genomic and epigenomic insights for the most complete view of cancer.\n## Now available within your Guardant360 Report:\n### Promoter Methylation\nAssess promoter methylation of 47 genes to identify more patients who may benefit from additional matched therapy options.\n### CHIP Filtering\nDistinguish CHIP variants with high accuracy for additional confidence in ctDNA results.\u00b9\n### Tumor Fraction Trend Line\nMonitor changes in tumor burden over time with a visual representation of tumor fraction across tests.\nCHIP: clonal hematopoiesis of indeterminate potential; ctDNA: circulating tumor DNA; IO: immunotherapy; PARP: poly (ADP-ribose) polymerase.\n**Important note**: Guardant360 was developed as a Laboratory Developed Test (LDT), and its performance characteristics were determined by the Guardant Health Clinical Laboratory in Redwood City, CA, USA, which is certified under the Clinical Laboratory Improvement Amendments of 1988 (CLIA) as qualified to perform high-complexity clinical testing. This test has not been cleared or approved by the US FDA.\n**References**: 1. Guardant Health data on file. 2024.\n17\n",
        "x-amz-bedrock-kb-document-page-number": 16.0,
        "x-amz-bedrock-kb-source-uri": "s3://consiergeai-salesrep-training/salesrep/Webinar G360 updates 12_24_CHIP_Promoter_Methylation.pdf"
      }
    },
    {
      "metadata": {
        "department": "S&M",
        "region": "US",
        "x-amz-bedrock-kb-byte-content-source": "s3://consiergeai-salesrep-training/aws/bedrock/knowledge_bases/WYAHSIZEAR/4HILUSLBPF/627cb956-e61c-4b12-a2a4-2f50eb1f1e51.png",
        "x-amz-bedrock-kb-data-source-id": "4HILUSLBPF",
        "x-amz-bedrock-kb-description": "# New features coming to Guardant360\nWhat customers have been asking for, plus more visible results from our differentiated epigenomic panel\n<figure>\nA large white checkmark/stylized \"G\" logo on a blue background, representing the Guardant Health brand\n</figure>\n| | Description |\n|-|-|\n| Promoter Methylation | Assess promoter methylation of 47 genes |\n| CHIP Filtering | Distinguish CHIP variants with high accuracy |\n| Tumor Fraction Trend Line | Monitor changes in tumor burden over time with a visual representation of tumor fraction across tests |\n## Other updates:\n* Gene count expanding from 739 to 740 (addition of *MGMT*)\n* Lower limit of quantification (LoQ) (now aligns with Guardant Reveal at 0.05%)\n**ALSO APPROVED BY NYS!**\n6\n",
        "x-amz-bedrock-kb-document-page-number": 5.0,
        "x-amz-bedrock-kb-source-uri": "s3://consiergeai-salesrep-training/salesrep/November_24_Eaglet_Meeting.pdf"
      }
    },
    
  ]

import boto3
s3 = boto3.client('s3', region_name='us-west-2')  # specify your region

def get_presigned_url(bucket, key, expiration=3600):
    return s3.generate_presigned_url(
        'get_object', 
        Params={
            'Bucket': bucket, 
            'Key': key,
            'ResponseContentDisposition': 'inline',
        }, 
        ExpiresIn=expiration
)


def get_references_dict(parsed_refs):
    unique_refs = set(parsed_refs)  # to remove duplicates

    ## ger presigned urls for each reference
    presigned_urls = [get_presigned_url(ref.split('/')[2], '/'.join(ref.split('/')[3:])) for ref in unique_refs]

    # print(presigned_urls)
    # exit()



    ## get only the file names from the s3 paths
    filenames_only = [ref.split('/')[-1] for ref in unique_refs]

    ## {'filename': '', 'fileurl': ''}
    unique_refs_dict = [{'filename': file_name, 'fileurl': ref} for file_name, ref in zip(filenames_only, presigned_urls)]

    # print(unique_refs_dict)

    return unique_refs_dict

def get_references_dict_from_knowledge_sources(knowledge_sources):
    """
    Extracts references from knowledge sources and returns a dictionary with file names and presigned URLs.
    """
    parsed_refs = []
    for source in knowledge_sources:
        if 'x-amz-bedrock-kb-source-uri' in source['metadata']:
            parsed_refs.append(source['metadata']['x-amz-bedrock-kb-source-uri'])

    return get_references_dict(parsed_refs)

if __name__ == "__main__":
    # Example usage
    # parsed_refs = ['s3://conciergeai-salesrep-training/salesrep/Auto Replenishment FAQs.docx', 's3://conciergeai-salesrep-training/salesrep/Automated Kit Replenishment Field Overview for Roll-out.pdf', 's3://conciergeai-salesrep-training/salesrep/Auto Replenishment FAQs.docx', 's3://conciergeai-salesrep-training/salesrep/Automated Kit Replenishment Field Overview for Roll-out.pdf']
    # parsed_refs = [
    #     's3://conciergeai-salesrep-training/salesrep/Auto Replenishment FAQs.docx',
    #     's3://conciergeai-salesrep-training/salesrep/Automated Kit Replenishment Field Overview for Roll-out.pdf',
    #     's3://conciergeai-salesrep-training/salesrep/Auto Replenishment FAQs.docx',
    #     's3://conciergeai-salesrep-training/salesrep/Automated Kit Replenishment Field Overview for Roll-out.pdf'
    # ]

    # for ref in parsed_refs:
    #     print(ref.split('/')[2], '/'.join(ref.split('/')[3:])) 

    # references_dict = get_references_dict(parsed_refs)
    # print(references_dict)

    # Get references from knowledge sources
    # knowledge_sources = [...]  # your knowledge sources here
    references_dict = get_references_dict_from_knowledge_sources(knowledge_sources) 
    print(references_dict)