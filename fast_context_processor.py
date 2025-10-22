"""
Fast Context Processor - Optimized for speed over completeness
"""

from weaviate_context_processor import WeaviateContextProcessor
from typing import Dict, Any, List
import asyncio

class FastContextProcessor(WeaviateContextProcessor):
    """
    Optimized version of WeaviateContextProcessor for speed
    - Processes only the most important fields
    - Uses smaller batch sizes
    - Skips less critical extractions
    """
    
    def enhance_extracted_data_with_context_fast(self, structured_data: Dict[str, Any], llm_results: Dict[str, Any], document_id: str) -> Dict[str, Any]:
        """
        FAST MODE: Enhance only the most important fields for speed
        
        Args:
            structured_data: Original structured data from Textract
            llm_results: Results from LLM field extraction
            document_id: Document ID in Weaviate
            
        Returns:
            Enhanced results with polished context (limited fields)
        """
        print("Starting FAST MODE Weaviate + LLM context enhancement...")
        
        enhanced_results = llm_results.copy()
        
        # Only process the first table and most important fields
        important_keywords = ['revenue', 'profit', 'growth', 'margin', 'cash', 'earnings', 'sales']
        
        # Collect only important fields
        important_field_contexts = []
        field_mappings = []
        
        # Process only first table and only important fields
        tables = enhanced_results.get("processed_tables", [])
        if tables:
            table = tables[0]  # Only first table
            if "structured_table" in table and isinstance(table["structured_table"], dict):
                for field_name, field_value in table["structured_table"].items():
                    if (field_name != "error" and field_value and 
                        any(keyword in field_name.lower() for keyword in important_keywords)):
                        
                        # Quick search with limit 1 for speed
                        relevant_chunks = self.search_relevant_context(
                            field_name, field_value, document_id, limit=1
                        )
                        
                        important_field_contexts.append({
                            "field_name": field_name,
                            "field_value": field_value,
                            "raw_context": "",
                            "relevant_chunks": relevant_chunks
                        })
                        
                        field_mappings.append({
                            "type": "table",
                            "index": 0,
                            "field": field_name
                        })
                        
                        # Limit to max 5 fields for speed
                        if len(important_field_contexts) >= 5:
                            break
        
        # Skip KV pairs and document text for maximum speed
        
        # Batch process important contexts only
        if important_field_contexts:
            print(f"FAST MODE: Processing {len(important_field_contexts)} important fields...")
            
            polished_contexts = asyncio.run(self.polish_context_batch_async(important_field_contexts))
            
            # Apply results back
            for i, mapping in enumerate(field_mappings):
                if i < len(polished_contexts):
                    polished_context = polished_contexts[i]
                    
                    if mapping["type"] == "table":
                        table = enhanced_results["processed_tables"][mapping["index"]]
                        if "polished_context" not in table:
                            table["polished_context"] = {}
                        table["polished_context"][mapping["field"]] = polished_context
        
        print("FAST MODE Weaviate + LLM context enhancement completed")
        return enhanced_results


def process_structured_data_with_llm_fast(structured_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    FAST MODE: Process with optimized context enhancement
    """
    from structured_llm_processor import process_structured_data_with_llm_async, cost_tracker
    from context_tracker import integrate_context_tracking
    
    # Run the async processing
    result = asyncio.run(process_structured_data_with_llm_async(structured_data))
    
    # Skip context tracking for speed
    print("Skipping context tracking in FAST MODE")
    
    # Fast Weaviate enhancement
    try:
        fast_processor = FastContextProcessor()
        
        document_text = structured_data.get('document_text', [])
        if document_text and fast_processor.connected:
            document_id = fast_processor.store_document_chunks(document_text)
            
            # Use fast enhancement
            result = fast_processor.enhance_extracted_data_with_context_fast(
                structured_data, result, document_id
            )
            
            result["weaviate_enhancement"] = {
                "document_id": document_id,
                "chunks_stored": len(document_text),
                "enhancement_completed": True,
                "mode": "FAST"
            }
            
            print(f"FAST MODE Weaviate enhancement completed for document {document_id}")
        else:
            result["weaviate_enhancement"] = {
                "enhancement_completed": False,
                "error": "No document text or Weaviate not connected",
                "mode": "FAST"
            }
            
    except Exception as e:
        print(f"FAST MODE Weaviate enhancement failed: {e}")
        result["weaviate_enhancement"] = {
            "enhancement_completed": False,
            "error": str(e),
            "mode": "FAST"
        }
    
    return result