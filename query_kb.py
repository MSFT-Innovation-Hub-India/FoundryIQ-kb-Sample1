"""Interactive Query Interface for Knowledge Base.

This script provides an interactive console interface for querying the knowledge base.
It accepts natural language questions from users and retrieves answers using the
agentic retrieval pipeline with answer synthesis.

The knowledge base queries multiple sources:
- Contoso Insurance FAQ index
- Contoso Retail index
- Contoso Gaming index
- Bing web search (for real-time web data)

The system uses Azure OpenAI to:
1. Plan which knowledge sources to query
2. Formulate optimized search queries
3. Synthesize coherent answers from retrieved documents
4. Include citations and references

Environment Variables Required:
    search_url: Azure AI Search service endpoint
    search_api_key: API key for Azure AI Search
    index_insurance: Name of the insurance FAQ index
    index_retail: Name of the retail index
    index_gaming: Name of the gaming index

Prerequisites:
    - Knowledge base must be created (run create_kb.py)
    - All knowledge sources must exist
    - Azure OpenAI must be configured with valid credentials

Usage:
    python query_kb.py
    
    Then enter your questions at the prompt.
    Type 'exit', 'quit', or 'q' to end the session.

Example Queries:
    - "What insurance policies does Contoso offer?"
    - "Tell me about Contoso retail products"
    - "What games are available from Contoso?"
    - "What's the latest news on artificial intelligence?" (uses web search)
"""

import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.knowledgebases import KnowledgeBaseRetrievalClient
from azure.search.documents.knowledgebases.models import (
    KnowledgeBaseMessage,
    KnowledgeBaseMessageTextContent,
    KnowledgeBaseRetrievalRequest,
    SearchIndexKnowledgeSourceParams
)

# Load environment variables from .env file
load_dotenv()

# Get configuration from environment variables
search_url = os.getenv("search_url")
search_api_key = os.getenv("search_api_key")
index_insurance = os.getenv("index_insurance", "contoso-insurance-faq-index")
index_retail = os.getenv("index_retail", "contoso-retail-index")
index_gaming = os.getenv("index_gaming", "contoso-gaming-index")
knowledge_base_name = "contoso-multi-index-kb"

# Create knowledge base retrieval client
kb_client = KnowledgeBaseRetrievalClient(
    endpoint=search_url,
    knowledge_base_name=knowledge_base_name,
    credential=AzureKeyCredential(search_api_key)
)

print("=" * 80)
print("Knowledge Base Query Interface")
print("=" * 80)
print(f"Connected to: {search_url}")
print(f"Knowledge Base: {knowledge_base_name}")
print("\nThis knowledge base includes:")
print("  • Contoso Insurance FAQ")
print("  • Contoso Retail")
print("  • Contoso Gaming")
print("  • Bing Web Search (real-time web data)")
print("\nType your questions and press Enter.")
print("Type 'exit' or 'quit' to end the session.\n")
print("=" * 80)

# Interactive query loop
while True:
    # Get user input
    user_query = input("\nYour question: ").strip()
    
    # Check for exit commands
    if user_query.lower() in ['exit', 'quit', 'q']:
        print("\nThank you for using the Knowledge Base Query Interface!")
        break
    
    # Skip empty queries
    if not user_query:
        continue
    
    try:
        # Create retrieval request
        request = KnowledgeBaseRetrievalRequest(
            messages=[
                KnowledgeBaseMessage(
                    role="user",
                    content=[KnowledgeBaseMessageTextContent(text=user_query)]
                )
            ],
            knowledge_source_params=[
                SearchIndexKnowledgeSourceParams(
                    knowledge_source_name=index_insurance,
                    include_references=True,
                    include_reference_source_data=True,
                    always_query_source=False
                ),
                SearchIndexKnowledgeSourceParams(
                    knowledge_source_name=index_retail,
                    include_references=True,
                    include_reference_source_data=True,
                    always_query_source=False
                ),
                SearchIndexKnowledgeSourceParams(
                    knowledge_source_name=index_gaming,
                    include_references=True,
                    include_reference_source_data=True,
                    always_query_source=False
                )
            ],
            include_activity=True
        )
        
        # Send request to knowledge base
        print("\nSearching knowledge base...")
        result = kb_client.retrieve(request)
        
        # Display response
        print("\n" + "=" * 80)
        print("ANSWER")
        print("=" * 80)
        if result.response and len(result.response) > 0:
            for response_item in result.response:
                if response_item.content:
                    for content_item in response_item.content:
                        if hasattr(content_item, 'text'):
                            print(content_item.text)
                            print()
        else:
            print("No answer found.")
        
        # Display references/citations if available
        if hasattr(result, 'references') and result.references:
            print("\n" + "=" * 80)
            print("CITATIONS")
            print("=" * 80)
            for idx, ref in enumerate(result.references):
                print(f"\n[ref_id:{idx}]")
                print("-" * 80)
                
                # Display knowledge source type
                source_type = getattr(ref, 'type', 'unknown')
                print(f"Source Type: {source_type}")
                
                # Handle web sources differently from search index sources
                if source_type == 'web':
                    # Web source - get URL and snippet from source_data
                    if hasattr(ref, 'source_data') and ref.source_data:
                        if isinstance(ref.source_data, dict):
                            url = ref.source_data.get('url', 'Unknown URL')
                            title = ref.source_data.get('name', 'Web Source')
                            snippet = ref.source_data.get('snippet', '')
                            
                            print(f"Title: {title}")
                            print(f"URL: {url}")
                            
                            if snippet:
                                print(f"\nCitation Text:")
                                print("-" * 80)
                                print(snippet)
                            else:
                                print("\nNo snippet available for this web source.")
                    else:
                        print("No source data available for this web reference.")
                
                elif source_type == 'searchIndex':
                    # Search index source - get document and content
                    if hasattr(ref, 'additional_properties') and isinstance(ref.additional_properties, dict):
                        title = ref.additional_properties.get('title', 'Unknown')
                        print(f"Document: {title}")
                    
                    # Display reranker score if available (only for search indexes)
                    if hasattr(ref, 'reranker_score') and ref.reranker_score is not None:
                        print(f"Relevance Score: {ref.reranker_score:.4f}")
                    
                    # Extract and display content from source_data
                    if hasattr(ref, 'source_data') and ref.source_data:
                        if isinstance(ref.source_data, dict):
                            content = ref.source_data.get('content')
                            if content:
                                print(f"\nCitation Text:")
                                print("-" * 80)
                                # Clean up the content formatting
                                content_text = content.replace('\r\n', '\n').replace('\t', '  ')
                                print(content_text)
                            else:
                                print("\nNo content available for this reference.")
                    else:
                        print("\nNo source data available for this reference.")
                
                else:
                    # Unknown source type - display whatever is available
                    print(f"Unknown source type: {source_type}")
                    if hasattr(ref, 'source_data') and ref.source_data:
                        print(f"Source Data: {ref.source_data}")
            
            print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Please try a different question.")

print()
