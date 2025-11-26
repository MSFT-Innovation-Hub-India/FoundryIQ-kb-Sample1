"""List All Indexes in Azure AI Search Service.

This utility script lists all search indexes available in the Azure AI Search service.
Useful for discovering existing indexes before creating knowledge sources.

Environment Variables Required:
    search_url: Azure AI Search service endpoint

Authentication:
    Uses DefaultAzureCredential (managed identity or Azure CLI credentials)

Usage:
    python list_indexes.py

Output:
    Displays a list of all index names in the search service.
"""

import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient

# Load environment variables from .env file
load_dotenv()

# Get configuration from environment variables
search_url = os.getenv("search_url")

# Use DefaultAzureCredential for managed identity authentication
credential = DefaultAzureCredential()

# Create search index client
index_client = SearchIndexClient(endpoint=search_url, credential=credential)

# List all indexes
print(f"Listing indexes in: {search_url}\n")
indexes = index_client.list_indexes()

print("Available indexes:")
for index in indexes:
    print(f"  - {index.name}")
