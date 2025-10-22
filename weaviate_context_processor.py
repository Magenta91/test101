import weaviate
import json
import os
import re
from typing import Dict, Any, List, Optional
from openai import OpenAI
from dotenv import load_dotenv
import uuid
import time

load_dotenv()

class WeaviateContextProcessor:
    def __init__(self):
        """Initialize Weaviate client and OpenAI client"""
        try:
            self.client = weaviate.Client("http://localhost:8080")
            self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            self.schema_name = "DocumentChunk"
            self._setup_schema()
            self.connected = True
        except Exception as e:
            print(f"Weaviate connection failed: {e}")
            self.connected = False
            self.client = None
            self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY")) if os.environ.get("OPENAI_API_KEY") else None
    
    def _setup_schema(self):
        """Setup Weaviate schema for document chunks"""
        schema = {
            "classes": [
                {
                    "class": self.schema_name,
                    "description": "Document text chunks for context retrieval",
                    "vectorizer": "text2vec-openai",
                    "moduleConfig": {
                        "text2vec-openai": {
                            "model": "ada",
                            "modelVersion": "002",
                            "type": "text"
                        }
                    },
                    "properties": [
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "The text content of the chunk"
                        },
                        {
                            "name": "chunk_id",
                            "dataType": ["string"],
                            "description": "Unique identifier for the chunk"
                        },
                        {
                            "name": "document_id",
                            "dataType": ["string"],
                            "description": "Document identifier this chunk belongs to"
                        },
                        {
                            "name": "chunk_index",
                            "dataType": ["int"],
                            "description": "Index of this chunk in the document"
                        },
                        {
                            "name": "chunk_type",
                            "dataType": ["string"],
                            "description": "Type of chunk: sentence, paragraph, or section"
                        }
                    ]
                }
            ]
        }
        
        # Delete existing schema if it exists
        try:
            self.client.schema.delete_class(self.schema_name)
            print(f"Deleted existing {self.schema_name} schema")
        except:
            pass
        
        # Create new schema
        self.client.schema.create(schema)
        print(f"Created {self.schema_name} schema")
    
    def chunk_document_text(self, document_text: List[str], document_id: str) -> List[Dict[str, Any]]:
        """
        Chunk document text into meaningful pieces for vector storage
        
        Args:
            document_text: List of text lines from document
            document_id: Unique identifier for this document
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        current_chunk = []
        chunk_index = 0
        
        # Join lines into full text first
        full_text = " ".join(document_text)
        
        # Split into sentences using regex
        sentences = re.split(r'(?<=[.!?])\s+', full_text)
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Create individual sentence chunks (for precise matching)
            if len(sentence) > 20:  # Skip very short fragments
                chunks.append({
                    "content": sentence,
                    "chunk_id": f"{document_id}_sentence_{i}",
                    "document_id": document_id,
                    "chunk_index": i,
                    "chunk_type": "sentence"
                })
            
            # Also create paragraph chunks (for broader context)
            current_chunk.append(sentence)
            
            # Create paragraph chunk every 3-5 sentences
            if len(current_chunk) >= 4 or i == len(sentences) - 1:
                paragraph_content = " ".join(current_chunk)
                if len(paragraph_content) > 50:
                    chunks.append({
                        "content": paragraph_content,
                        "chunk_id": f"{document_id}_paragraph_{chunk_index}",
                        "document_id": document_id,
                        "chunk_index": chunk_index,
                        "chunk_type": "paragraph"
                    })
                    chunk_index += 1
                current_chunk = []
        
        print(f"Created {len(chunks)} chunks for document {document_id}")
        return chunks
    
    def store_document_chunks(self, document_text: List[str], document_id: str = None) -> str:
        """
        Store document chunks in Weaviate
        
        Args:
            document_text: List of text lines from document
            document_id: Optional document ID, will generate if not provided
            
        Returns:
            Document ID used for storage
        """
        if not self.connected:
            print("Weaviate not connected, skipping chunk storage")
            return "no_connection"
            
        if not document_id:
            document_id = f"doc_{uuid.uuid4().hex[:8]}"
        
        # Clear any existing chunks for this document
        self.clear_document_chunks(document_id)
        
        # Create chunks
        chunks = self.chunk_document_text(document_text, document_id)
        
        # Store chunks in Weaviate
        print(f"Storing {len(chunks)} chunks in Weaviate...")
        
        with self.client.batch as batch:
            batch.batch_size = 100
            
            for chunk in chunks:
                batch.add_data_object(
                    data_object={
                        "content": chunk["content"],
                        "chunk_id": chunk["chunk_id"],
                        "document_id": chunk["document_id"],
                        "chunk_index": chunk["chunk_index"],
                        "chunk_type": chunk["chunk_type"]
                    },
                    class_name=self.schema_name
                )
        
        print(f"Successfully stored document {document_id} in Weaviate")
        return document_id
    
    def clear_document_chunks(self, document_id: str):
        """Clear all chunks for a specific document"""
        if not self.connected:
            return
            
        try:
            self.client.batch.delete_objects(
                class_name=self.schema_name,
                where={
                    "path": ["document_id"],
                    "operator": "Equal",
                    "valueString": document_id
                }
            )
            print(f"Cleared existing chunks for document {document_id}")
        except Exception as e:
            print(f"Note: Could not clear existing chunks: {e}")
    
    def search_relevant_context(self, field_name: str, field_value: str, document_id: str, limit: int = 5) -> List[str]:
        """
        Search for relevant context chunks for a specific field
        
        Args:
            field_name: Name of the field (e.g., "Revenue")
            field_value: Value of the field (e.g., "$125.3M")
            document_id: Document to search within
            limit: Maximum number of chunks to return
            
        Returns:
            List of relevant text chunks
        """
        if not self.connected:
            print(f"Weaviate not connected, returning empty context for {field_name}")
            return []
            
        # Clean field value for better matching
        clean_value = re.sub(r'[^\w\s\.]', ' ', str(field_value))
        
        # Create search query
        search_queries = [
            f"{field_name} {clean_value}",  # Direct field + value
            f"{field_name}",  # Just field name
            f"{clean_value}",  # Just value
        ]
        
        all_results = []
        
        for query in search_queries:
            try:
                # Semantic search using Weaviate
                result = (
                    self.client.query
                    .get(self.schema_name, ["content", "chunk_type", "chunk_id"])
                    .with_near_text({"concepts": [query]})
                    .with_where({
                        "path": ["document_id"],
                        "operator": "Equal",
                        "valueString": document_id
                    })
                    .with_limit(limit)
                    .with_additional(["distance"])
                    .do()
                )
                
                if result.get("data", {}).get("Get", {}).get(self.schema_name):
                    chunks = result["data"]["Get"][self.schema_name]
                    for chunk in chunks:
                        # Add relevance score based on distance (lower distance = higher relevance)
                        distance = chunk.get("_additional", {}).get("distance", 1.0)
                        relevance_score = 1.0 - distance
                        
                        all_results.append({
                            "content": chunk["content"],
                            "chunk_type": chunk["chunk_type"],
                            "chunk_id": chunk["chunk_id"],
                            "relevance_score": relevance_score,
                            "query": query
                        })
                        
            except Exception as e:
                print(f"Search error for query '{query}': {e}")
                continue
        
        # Remove duplicates and sort by relevance
        unique_results = {}
        for result in all_results:
            chunk_id = result["chunk_id"]
            if chunk_id not in unique_results or result["relevance_score"] > unique_results[chunk_id]["relevance_score"]:
                unique_results[chunk_id] = result
        
        # Sort by relevance score and return top results
        sorted_results = sorted(unique_results.values(), key=lambda x: x["relevance_score"], reverse=True)
        
        # Return just the content strings
        relevant_chunks = [r["content"] for r in sorted_results[:limit]]
        
        print(f"Found {len(relevant_chunks)} relevant chunks for {field_name}: {field_value}")
        return relevant_chunks
    
    def polish_context_with_llm(self, field_name: str, field_value: str, raw_context: str, relevant_chunks: List[str]) -> str:
        """
        Use LLM to polish the context using relevant chunks from Weaviate
        
        Args:
            field_name: Name of the field
            field_value: Value of the field  
            raw_context: Original context from function-based extraction
            relevant_chunks: Relevant chunks from Weaviate search
            
        Returns:
            Polished context string
        """
        if not relevant_chunks:
            return raw_context  # Fallback to original if no relevant chunks found
        
        if not self.openai_client:
            print(f"OpenAI client not available, returning original context for {field_name}")
            return raw_context
        
        # Prepare relevant chunks text
        chunks_text = "\n".join([f"- {chunk}" for chunk in relevant_chunks])
        
        prompt = f"""You are a document analysis expert. Your task is to create a polished, accurate context for a specific data field.

FIELD: {field_name}
VALUE: {field_value}

CURRENT CONTEXT (from automated extraction):
{raw_context}

RELEVANT DOCUMENT EXCERPTS (from semantic search):
{chunks_text}

INSTRUCTIONS:
1. Create a clean, polished context that explains this specific field and value
2. Use ONLY information from the document excerpts above - do not add external information
3. Focus on the specific field and value mentioned
4. Make the context complete and well-formatted
5. If the current context is already good, you may keep it but improve formatting
6. If you find better explanatory text in the excerpts, use that instead
7. Ensure the context is a complete sentence or paragraph

REQUIREMENTS:
- Must be factually accurate (only use provided excerpts)
- Must be relevant to the specific field and value
- Must be well-formatted and professional
- Should be 1-3 sentences maximum
- Do not hallucinate or add information not in the excerpts

Return only the polished context text, nothing else."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=200    # Keep responses concise
            )
            
            polished_context = response.choices[0].message.content.strip()
            
            # Validation: ensure the polished context isn't empty or generic
            if len(polished_context) < 10 or "I cannot" in polished_context or "not provided" in polished_context.lower():
                print(f"LLM polishing failed for {field_name}, using original context")
                return raw_context
            
            print(f"Successfully polished context for {field_name}")
            return polished_context
            
        except Exception as e:
            print(f"Error polishing context for {field_name}: {e}")
            return raw_context  # Fallback to original context
    
    async def polish_context_batch_async(self, field_contexts: List[Dict[str, Any]]) -> List[str]:
        """
        Polish multiple contexts in a single LLM call for efficiency
        
        Args:
            field_contexts: List of dicts with field_name, field_value, raw_context, relevant_chunks
            
        Returns:
            List of polished contexts in same order
        """
        if not field_contexts or not self.openai_client:
            return [""] * len(field_contexts)
        
        # Limit batch size to avoid token limits
        if len(field_contexts) > 8:
            field_contexts = field_contexts[:8]
        
        # Build batch prompt
        batch_items = []
        for i, item in enumerate(field_contexts):
            chunks_text = "\n".join([f"  - {chunk}" for chunk in item.get("relevant_chunks", [])])
            batch_items.append(f"""
{i+1}. FIELD: {item['field_name']}
   VALUE: {item['field_value']}
   CURRENT CONTEXT: {item.get('raw_context', '')}
   RELEVANT EXCERPTS:
{chunks_text}""")
        
        batch_prompt = f"""You are a document analysis expert. Polish the context for each field below using ONLY the provided excerpts.

FIELDS TO PROCESS:
{''.join(batch_items)}

INSTRUCTIONS:
1. For each field, create a clean, polished context (1-2 sentences max)
2. Use ONLY information from the relevant excerpts - no external information
3. Focus on the specific field and value mentioned
4. If no good context can be created, return empty string for that field

Return JSON array with polished contexts in order:
["context for field 1", "context for field 2", ...]

Example: ["Revenue grew 15% to $125M driven by strong performance", "Net profit increased significantly to $46.7M"]"""

        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            response = await loop.run_in_executor(
                None, 
                lambda: self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": batch_prompt}],
                    temperature=0.1,
                    max_tokens=400,
                    response_format={"type": "json_object"}
                )
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            try:
                polished_contexts = json.loads(content)
                if isinstance(polished_contexts, list):
                    # Pad with empty strings if needed
                    while len(polished_contexts) < len(field_contexts):
                        polished_contexts.append("")
                    return polished_contexts[:len(field_contexts)]
            except json.JSONDecodeError:
                pass
            
            # Fallback: return original contexts
            return [item.get('raw_context', '') for item in field_contexts]
            
        except Exception as e:
            print(f"Batch polishing failed: {e}")
            return [item.get('raw_context', '') for item in field_contexts]

    def enhance_extracted_data_with_context(self, structured_data: Dict[str, Any], llm_results: Dict[str, Any], document_id: str) -> Dict[str, Any]:
        """
        Enhance the extracted data with polished context using Weaviate + LLM (OPTIMIZED)
        
        Args:
            structured_data: Original structured data from Textract
            llm_results: Results from LLM field extraction
            document_id: Document ID in Weaviate
            
        Returns:
            Enhanced results with polished context
        """
        print("Starting OPTIMIZED Weaviate + LLM context enhancement...")
        
        enhanced_results = llm_results.copy()
        
        # Collect all fields for batch processing
        all_field_contexts = []
        field_mappings = []  # Track where each field belongs
        
        # Collect from tables
        for table_idx, table in enumerate(enhanced_results.get("processed_tables", [])):
            if "structured_table" in table and isinstance(table["structured_table"], dict):
                for field_name, field_value in table["structured_table"].items():
                    if field_name != "error" and field_value:
                        # Quick search for relevant context
                        relevant_chunks = self.search_relevant_context(
                            field_name, field_value, document_id, limit=2  # Reduced from 3 to 2
                        )
                        
                        original_context = table.get("commentary", {}).get(f"field_{field_name}", "")
                        
                        all_field_contexts.append({
                            "field_name": field_name,
                            "field_value": field_value,
                            "raw_context": original_context,
                            "relevant_chunks": relevant_chunks
                        })
                        
                        field_mappings.append({
                            "type": "table",
                            "index": table_idx,
                            "field": field_name
                        })
        
        # Collect from key-values (limit to important ones)
        kv_data = enhanced_results.get("processed_key_values", {}).get("structured_key_values", {})
        if isinstance(kv_data, dict):
            # Only process first 5 KV pairs to save time
            kv_items = list(kv_data.items())[:5]
            for field_name, field_value in kv_items:
                if field_name != "error" and field_value:
                    relevant_chunks = self.search_relevant_context(
                        field_name, field_value, document_id, limit=2
                    )
                    
                    all_field_contexts.append({
                        "field_name": field_name,
                        "field_value": field_value,
                        "raw_context": "",
                        "relevant_chunks": relevant_chunks
                    })
                    
                    field_mappings.append({
                        "type": "kv",
                        "field": field_name
                    })
        
        # Skip document text extracts for speed (they're usually less important)
        
        # Batch process all contexts
        if all_field_contexts:
            print(f"Batch processing {len(all_field_contexts)} fields...")
            
            import asyncio
            polished_contexts = asyncio.run(self.polish_context_batch_async(all_field_contexts))
            
            # Apply results back to original structure
            for i, mapping in enumerate(field_mappings):
                if i < len(polished_contexts):
                    polished_context = polished_contexts[i]
                    
                    if mapping["type"] == "table":
                        table = enhanced_results["processed_tables"][mapping["index"]]
                        if "polished_context" not in table:
                            table["polished_context"] = {}
                        table["polished_context"][mapping["field"]] = polished_context
                        
                    elif mapping["type"] == "kv":
                        if "polished_context" not in enhanced_results["processed_key_values"]:
                            enhanced_results["processed_key_values"]["polished_context"] = {}
                        enhanced_results["processed_key_values"]["polished_context"][mapping["field"]] = polished_context
        
        print("OPTIMIZED Weaviate + LLM context enhancement completed")
        return enhanced_results


def test_weaviate_setup():
    """Test function to verify Weaviate is working"""
    try:
        processor = WeaviateContextProcessor()
        
        if not processor.connected:
            print("Weaviate not connected")
            return False
        
        # Test document
        test_doc = [
            "Revenue grew by 15% year-on-year reaching AUD 125.3 million.",
            "Net profit after tax increased 12% YoY to AUD 46.7mn (1HFY22: AUD 41.7mn).",
            "The company reported strong performance across all segments.",
            "Operating expenses were well controlled at $78.6 million."
        ]
        
        # Store test document
        doc_id = processor.store_document_chunks(test_doc, "test_doc")
        
        # Test search
        results = processor.search_relevant_context("Revenue", "125.3 million", doc_id)
        print(f"Search results: {len(results)} chunks found")
        
        # Test polishing
        if results:
            polished = processor.polish_context_with_llm(
                "Revenue", "125.3 million", 
                "Revenue increased significantly", 
                results
            )
            print(f"Polished context: {polished}")
        
        return True
        
    except Exception as e:
        print(f"Weaviate test failed: {e}")
        return False


if __name__ == "__main__":
    test_weaviate_setup()