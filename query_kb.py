"""Interactive console interface for the knowledge base."""

from kb_query_service import execute_kb_query, get_kb_configuration

print("=" * 80)
print("Knowledge Base Query Interface")
print("=" * 80)
config = get_kb_configuration()
print(f"Connected to: {config['searchEndpoint']}")
print(f"Knowledge Base: {config['knowledgeBaseName']}")
print("\nThis knowledge base includes:")
for idx_name in config["indexes"]:
    print(f"  • {idx_name}")
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
        print("\nSearching knowledge base...")
        query_result = execute_kb_query(user_query)
        
        # Display response
        print("\n" + "=" * 80)
        print("ANSWER")
        print("=" * 80)
        answers = query_result.get("answers", [])
        if answers:
            for answer_text in answers:
                print(answer_text)
                print()
        else:
            print("No answer found.")
        
        # Display references/citations if available
        citations = query_result.get("citations", [])
        if citations:
            print("\n" + "=" * 80)
            print("CITATIONS")
            print("=" * 80)
            for citation in citations:
                print(f"\n[ref_id:{citation['id']}]")
                print("-" * 80)
                
                source_type = citation.get("type", "unknown")
                print(f"Source Type: {source_type}")

                title = citation.get("title") or citation.get("document") or "Unknown"
                if title:
                    print(f"Title: {title}")

                if citation.get("url"):
                    print(f"URL: {citation['url']}")

                if citation.get("relevanceScore") is not None:
                    print(f"Relevance Score: {citation['relevanceScore']:.4f}")

                citation_text = citation.get("citationText")
                if citation_text:
                    print(f"\nCitation Text:")
                    print("-" * 80)
                    print(citation_text)
                elif citation.get("note"):
                    print(f"\nNote: {citation['note']}")
            
            print("\n" + "=" * 80)
        else:
            print("\n" + "=" * 80)
            print("CITATIONS")
            print("=" * 80)
            print("No citations were returned for this answer.")
            print("\n" + "=" * 80)
        
        # Display timing information
        timing = query_result.get("timing", {})
        print("\n" + "=" * 80)
        print("PERFORMANCE METRICS")
        print("=" * 80)
        total_time = timing.get("total", 0.0)
        request_time = timing.get("requestPreparation", 0.0)
        retrieval_time = timing.get("kbRetrieval", 0.0)
        processing_time = timing.get("responseProcessing", 0.0)
        pct = lambda value: (value / total_time * 100) if total_time else 0.0

        print(f"Total Query Time:           {total_time:.3f} seconds")
        print(f"  ├─ Request Preparation:   {request_time:.3f} seconds ({pct(request_time):.1f}%)")
        print(f"  ├─ KB Retrieval*:         {retrieval_time:.3f} seconds ({pct(retrieval_time):.1f}%)")
        print(f"  └─ Response Processing:   {processing_time:.3f} seconds ({pct(processing_time):.1f}%)")
        print(f"\n  *KB Retrieval includes: query planning, knowledge source")
        print(f"   selection, search execution, and answer synthesis by Azure OpenAI")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Please try a different question.")

print()
