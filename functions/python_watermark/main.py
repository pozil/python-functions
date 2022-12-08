import json
import base64
from io import BytesIO
from typing import Any

from salesforce_functions import Context, InvocationEvent, get_logger

import requests
from PIL import Image

# The type of the data payload sent with the invocation event.
# We're specifying a specific type for improved IDE auto-completion
# and linting coverage.
EventPayloadType = dict['docId': str]

logger = get_logger()


async def function(event: InvocationEvent[EventPayloadType], context: Context):
    """Applies a watermark on an image"""

    # Get latest version from document
    docId = event.data['docId']
    query = f"SELECT Id, PathOnClient, ContentDocumentId FROM ContentVersion WHERE ContentDocumentId='{docId}' AND IsLatest=true"
    result = await context.org.data_api.query(query)
    if len(result.records) == 0:
        raise Exception(f"Failed to find latest ContentVersion for doc {docId}")
    docVersion = result.records[0]

    # Download image
    logger.info(f"Downloading ContentVersion {docVersion.fields['Id']}")
    response = downloadFromSalesforce(context, docVersion.fields['Id'])
    
    # Edit image
    logger.info("Applying stamp")
    editedImageBytes = applyWatermarkOnImage(BytesIO(response.content))

    # Upload edited image
    logger.info(f"Uploading new ContentVersion for doc {docId}")
    response = uploadToSalesforce(context, docVersion, editedImageBytes)
    
    return response.json()


def applyWatermarkOnImage(originalContent: BytesIO):
    image = Image.open(originalContent)
    watermarkImage = Image.open("watermark.png")
    pasteCoords = (10, image.size[1] - watermarkImage.size[1] - 10) # Lower left
    image.paste(watermarkImage, pasteCoords, watermarkImage)
    editedContent = BytesIO()
    image.save(editedContent, "PNG")
    return editedContent


def downloadFromSalesforce(context: Context, docVersionId: str):
    accessToken = context.org.data_api.access_token
    headers = { 'Authorization': 'Bearer '+ accessToken }
    domainUrl = context.org.domain_url
    url = f"{domainUrl}/services/data/v56.0/sobjects/ContentVersion/{docVersionId}/VersionData"
    response = requests.get(url, headers = headers)
    if response.status_code != 200:
        raise Exception(f"Failed to download ContentVersion {docVersionId}: HTTP {response.status_code}")
    return response


def uploadToSalesforce(context: Context, docVersion: Any, content: BytesIO):
    accessToken = context.org.data_api.access_token
    headers = {
        'Authorization': 'Bearer '+ accessToken,
        'Content-Type': 'application/json'
    }
    domainUrl = context.org.domain_url
    url = f"{domainUrl}/services/data/v56.0/sobjects/ContentVersion"
    payload = {
        "ContentDocumentId" : docVersion.fields['ContentDocumentId'],
        "ReasonForChange" : "Stamped copy",
        "PathOnClient" : docVersion.fields['PathOnClient'],
        "VersionData": base64.b64encode(content.getvalue()).decode('utf-8')
    }
    response = requests.post(url,
        headers = headers,
        data = json.dumps(payload)
    )
    if response.status_code != 201:
        raise Exception(f"Failed to upload ContentVersion for doc {docVersion.fields['ContentDocumentId']}: HTTP {response.status_code}: {response.text}")
    return response
