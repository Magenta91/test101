import json
import os
from openai import OpenAI
from typing import Dict, Any, List
import asyncio
import aiohttp
import concurrent.futures
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Using gpt-4o-mini for optimal performance and cost efficiency
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# GPT-4o-mini pricing per 1M tokens (as of 2024)
GPT_4O_MINI_INPUT_COST = 0.150  # $0.150 per 1M input tokens
GPT_4O_MINI_OUTPUT_COST = 0.600  # $0.600 per 1M output tokens


class CostTracker:

    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.api_calls = 0

    def add_usage(self, input_tokens, output_tokens):
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.api_calls += 1

        input_cost = (input_tokens / 1_000_000) * GPT_4O_MINI_INPUT_COST
        output_cost = (output_tokens / 1_000_000) * GPT_4O_MINI_OUTPUT_COST
        call_cost = input_cost + output_cost
        self.total_cost += call_cost

        return call_cost

    def get_summary(self):
        return {
            'total_input_tokens':
            self.total_input_tokens,
            'total_output_tokens':
            self.total_output_tokens,
            'total_tokens':
            self.total_input_tokens + self.total_output_tokens,
            'total_cost_usd':
            round(self.total_cost, 6),
            'api_calls':
            self.api_calls,
            'input_cost_usd':
            round(
                (self.total_input_tokens / 1_000_000) * GPT_4O_MINI_INPUT_COST,
                6),
            'output_cost_usd':
            round((self.total_output_tokens / 1_000_000) *
                  GPT_4O_MINI_OUTPUT_COST, 6)
        }


# Global cost tracker instance
cost_tracker = CostTracker()


def split_text_section(text_lines, max_lines=25):
    """Split text lines into manageable chunks with sentence boundary preservation"""
    chunks = []
    current_chunk = []

    for i, line in enumerate(text_lines):
        current_chunk.append(line)

        # Check if we should create a chunk
        if len(current_chunk) >= max_lines:
            # Try to end at a sentence boundary
            if line.strip().endswith(('.', '!', '?', ':')):
                chunks.append(current_chunk)
                current_chunk = []
            elif len(
                    current_chunk) >= max_lines + 5:  # Force split if too long
                chunks.append(current_chunk)
                current_chunk = []

    # Add remaining lines
    if current_chunk:
        chunks.append(current_chunk)

    return chunks


async def process_table_data(table_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process table data with GPT-4o-mini asynchronously - simple format"""
    prompt = f"""Extract key data points from this table as simple field-value pairs.

Table data:
{json.dumps(table_data, indent=2)}

Instructions:
1. Extract important data points as field-value pairs
2. Use clear, descriptive field names
3. Focus on financial figures, dates, and key metrics
4. Keep it simple and straightforward

Return JSON with field-value pairs:
{{
  "Revenue": "value",
  "Growth_Rate": "value",
  "Date": "value"
}}"""

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                response_format={"type": "json_object"}))

        content = response.choices[0].message.content
        if content:
            result = json.loads(content)
        else:
            result = {"error": "No content received from OpenAI"}

        return {
            "page": table_data.get("page", 1),
            "structured_table": result,
            "original_rows": table_data.get("rows", [])
        }
    except Exception as e:
        print(f"Error processing table: {e}")
        return {
            "page": table_data.get("page", 1),
            "structured_table": {
                "error": str(e)
            },
            "original_rows": table_data.get("rows", [])
        }


async def process_key_value_data(
        key_value_pairs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process key-value pairs with GPT-4o-mini asynchronously"""
    prompt = f"""You are a data extraction specialist. Below are key-value pairs extracted from a document.

Extract and organize this information into clear field-value pairs. Focus on extracting actual data values like company names, dates, amounts, percentages, and other factual information.

Key-Value pairs:
{json.dumps(key_value_pairs, indent=2)}

Return a simple JSON object where each key is a descriptive field name and each value is the actual extracted data. Do not create nested structures or arrays. Provide the response as valid JSON format."""

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                response_format={"type": "json_object"}))

        # Track usage and cost
        if hasattr(response, 'usage') and response.usage:
            call_cost = cost_tracker.add_usage(
                response.usage.prompt_tokens, response.usage.completion_tokens)
            print(f"Key-value processing cost: ${call_cost:.6f}")

        content = response.choices[0].message.content
        if content:
            result = json.loads(content)
        else:
            result = {"error": "No content received from OpenAI"}

        return {
            "structured_key_values": result,
            "original_pairs": key_value_pairs
        }
    except Exception as e:
        print(f"Error processing key-value pairs: {e}")
        return {
            "structured_key_values": {
                "error": str(e)
            },
            "original_pairs": key_value_pairs
        }


async def process_text_chunk(text_chunk: List[str]) -> Dict[str, Any]:
    """Process a text chunk with GPT-4o-mini asynchronously and tabulate the content"""
    text_content = '\n'.join(text_chunk)

    prompt = f"""You are a financial document analyst. Extract and tabulate ALL meaningful data from this text segment.

Create a comprehensive table structure that captures the key information in a tabulated format.

Text:
{text_content}

Requirements:
1. Extract ALL meaningful data points and organize them into a table structure
2. Create appropriate column headers based on the content type
3. Structure data into logical rows and columns
4. Include financial metrics, dates, percentages, company info, etc.
5. If the text contains narrative information, extract key facts and tabulate them
6. IGNORE superscript numbers and footnote reference markers (¹²³ or (1)(2)(3) or [1][2][3])
7. Extract clean data values without footnote symbols

Return JSON with BOTH table structure AND individual facts:
{{
  "table_headers": ["Metric", "Value", "Period", "Context"],
  "table_rows": [
    ["Revenue", "$115.5M", "Q4 2023", "33% growth"],
    ["MAU", "65.8M", "Q4 2023", "Global users"],
    ["Market Share", "12%", "2023", "Primary market"]
  ],
  "extracted_facts": {{
    "Company_Name": "Life360",
    "Q4_Revenue": "$115.5 million",
    "MAU_Growth": "33%",
    "Market_Position": "Leading family safety platform"
  }}
}}

Extract comprehensive data - do not limit to just a few items. Return the response as valid JSON format."""

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                response_format={"type": "json_object"}))

        # Track usage and cost
        if hasattr(response, 'usage') and response.usage:
            call_cost = cost_tracker.add_usage(
                response.usage.prompt_tokens, response.usage.completion_tokens)
            print(f"Text chunk processing cost: ${call_cost:.6f}")

        content = response.choices[0].message.content
        if content:
            result = json.loads(content)
        else:
            result = {"error": "No content received from OpenAI"}

        return {
            "table_headers": result.get("table_headers", []),
            "table_rows": result.get("table_rows", []),
            "extracted_facts": result.get("extracted_facts", {}),
            "original_text": text_chunk
        }
    except Exception as e:
        print(f"Error processing text chunk: {e}")
        return {
            "extracted_facts": {
                "error": str(e)
            },
            "original_text": text_chunk
        }


async def match_commentary_to_data(row_data: str,
                                   text_chunks: List[str]) -> Dict[str, Any]:
    """Match document text commentary to table row data with strict relevance validation"""
    text_content = '\n'.join(text_chunks)

    prompt = f"""You are a strict document analysis expert. Your job is to find ONLY highly relevant commentary that directly explains a specific data point.

DATA POINT TO MATCH: {row_data}

DOCUMENT TEXT TO SEARCH:
{text_content}

ULTRA-STRICT MATCHING CRITERIA:
1. The commentary MUST specifically mention the exact field name, value, or closely related terms
2. The commentary MUST provide meaningful explanation, context, or analysis of THIS specific data point
3. The commentary MUST be a complete sentence or paragraph that makes sense on its own
4. REJECT any text that:
   - Only mentions the topic generally without the specific value
   - Starts mid-sentence or is incomplete
   - Talks about different data points or unrelated information
   - Is just a list item without explanation
   - Contains only the value without context

RELEVANCE SCORING:
- Score 0-10 where 10 = perfect match with specific explanation
- Only return commentary with score 8+ (highly relevant)
- If best match scores below 8, return null

Return JSON:
{{"commentary": "complete relevant explanation", "relevant": true, "relevance_score": 9}}
OR  
{{"commentary": null, "relevant": false, "relevance_score": 3}}

Be extremely selective - better to return no commentary than irrelevant commentary."""

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                response_format={"type": "json_object"}))

        content = response.choices[0].message.content
        if content:
            result = json.loads(content)
            return result
        else:
            return {"commentary": None, "relevant": False}

    except Exception as e:
        print(f"Error matching commentary: {e}")
        return {"commentary": None, "relevant": False}


async def process_structured_data_with_llm_async(
        structured_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process all sections of structured data with asynchronous LLM calls"""

    document_text = structured_data.get('document_text', [])
    tables = structured_data.get('tables', [])
    key_values = structured_data.get('key_values', [])

    results = {
        "processed_tables": [],
        "processed_key_values": {},
        "processed_document_text": [],
        "enhanced_data_with_commentary": [],
        "general_commentary": "",
        "summary": {
            "total_tables": len(tables),
            "total_key_values": len(key_values),
            "total_text_lines": len(document_text),
            "text_chunks_processed": 0,
            "commentary_matches": 0
        }
    }

    # Create tasks for asynchronous processing
    tasks = []

    # Process tables asynchronously
    if tables:
        print(f"Processing {len(tables)} tables asynchronously...")
        table_tasks = [process_table_data(table) for table in tables]
        tasks.extend(table_tasks)

    # Process key-value pairs
    if key_values:
        print(
            f"Processing {len(key_values)} key-value pairs asynchronously...")
        kv_task = process_key_value_data(key_values)
        tasks.append(kv_task)

    # Process document text in chunks
    text_tasks = []
    if document_text:
        text_chunks = split_text_section(document_text, max_lines=20)
        print(
            f"Processing document text in {len(text_chunks)} chunks asynchronously..."
        )
        text_tasks = [process_text_chunk(chunk) for chunk in text_chunks]
        tasks.extend(text_tasks)
        results["summary"]["text_chunks_processed"] = len(text_chunks)

    # Execute all tasks concurrently
    if tasks:
        print(f"Executing {len(tasks)} LLM processing tasks concurrently...")
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)

        # Organize results
        task_index = 0

        # Process table results
        if tables:
            for i in range(len(tables)):
                result = completed_tasks[task_index]
                if isinstance(result, Exception):
                    print(f"Table processing error: {result}")
                    result = {
                        "error": str(result),
                        "page": tables[i].get("page", 1)
                    }
                results["processed_tables"].append(result)
                task_index += 1

        # Process key-value result
        if key_values:
            result = completed_tasks[task_index]
            if isinstance(result, Exception):
                print(f"Key-value processing error: {result}")
                result = {"error": str(result)}
            results["processed_key_values"] = result
            task_index += 1

        # Process text chunk results
        if text_tasks:
            for i in range(len(text_tasks)):
                result = completed_tasks[task_index]
                if isinstance(result, Exception):
                    print(f"Text chunk processing error: {result}")
                    result = {"error": str(result)}
                results["processed_document_text"].append(result)
                task_index += 1

    # Phase 2: Enhanced data processing with commentary matching
    print("Starting commentary matching phase...")
    await process_commentary_matching(results, document_text)

    return results


async def process_commentary_matching(results: Dict[str, Any],
                                      document_text: List[str]) -> None:
    """Process commentary matching for all extracted data with optimized performance"""
    print("Starting optimized commentary matching phase...")
    
    # Skip commentary matching if document is too large or has too many data points
    total_data_points = 0
    for table in results.get("processed_tables", []):
        total_data_points += len(table.get("structured_table", {}).get("table_rows", []))
    
    if results.get("processed_key_values"):
        total_data_points += len(results["processed_key_values"].get("structured_key_values", {}))
    
    for chunk in results.get("processed_document_text", []):
        total_data_points += len(chunk.get("extracted_facts", {}))
    
    if total_data_points > 30 or len(document_text) > 150:
        print(f"Skipping commentary matching - too many items ({total_data_points} data points, {len(document_text)} text lines)")
        return
    
    # Process only the first few important data points sequentially
    processed_count = 0
    max_items = 8  # Limit total items processed
    
    # Process first table only
    if results.get("processed_tables") and processed_count < max_items:
        table = results["processed_tables"][0]
        for i, row in enumerate(table.get("structured_table", {}).get("table_rows", [])):
            if processed_count >= max_items or i >= 3:  # Max 3 rows per table
                break
            if isinstance(row, list) and len(row) >= 2:
                data_point = f"Field: {row[0]}, Value: {row[1]}"
                try:
                    commentary_result = await match_commentary_to_data(data_point, document_text[:30])
                    # Only add commentary if it's highly relevant (score 8+)
                    if (commentary_result.get("relevant") and 
                        commentary_result.get("commentary") and 
                        commentary_result.get("relevance_score", 0) >= 8):
                        if "commentary" not in table:
                            table["commentary"] = {}
                        table["commentary"][f"row_{i}"] = commentary_result["commentary"]
                        print(f"Added high-relevance commentary (score: {commentary_result.get('relevance_score')}) for {data_point}")
                    else:
                        print(f"Skipped low-relevance commentary (score: {commentary_result.get('relevance_score', 0)}) for {data_point}")
                    processed_count += 1
                except Exception as e:
                    print(f"Error matching commentary for table row: {e}")
                    break
    
    print(f"Commentary matching completed for {processed_count} items")


def process_structured_data_with_llm(
        structured_data: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous wrapper for asynchronous processing"""
    return asyncio.run(process_structured_data_with_llm_async(structured_data))
