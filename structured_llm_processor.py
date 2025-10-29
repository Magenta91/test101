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


def process_structured_data_with_llm_unified(structured_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Unified LLM extraction: Extracts field, value, and context together from all data sources.
    Optimized for maximum field extraction while maintaining data quality.
    """
    if not structured_data:
        return {"fields": {}}
    
    # Extract all data sources like legacy mode
    document_text = structured_data.get('document_text', [])
    tables = structured_data.get('tables', [])
    key_values = structured_data.get('key_values', [])
    
    # Convert document_text to string if it's a list
    if isinstance(document_text, list):
        text_content = '\n'.join(document_text)
    else:
        text_content = str(document_text)
    
    # Prepare comprehensive data for extraction with enhanced content organization
    all_data_sources = []
    
    # Add document text with enhanced structure
    if text_content.strip():
        # Organize text into logical sections for better extraction
        text_lines = text_content.split('\n')
        structured_text = "DOCUMENT TEXT (comprehensive analysis required):\n"
        
        # Process ALL text lines without grouping to avoid losing data
        for i, line in enumerate(text_lines):
            line = line.strip()
            if line:
                structured_text += f"LINE {i+1}: {line}\n"
        
        structured_text += "\nEXTRACT ALL DATA FROM EVERY LINE ABOVE\n"
        
        all_data_sources.append(structured_text)
    
    # Add comprehensive table data with enhanced extraction focus
    if tables:
        table_content = "TABLES (extract ALL data points - each cell, header, and relationship):\n"
        for i, table in enumerate(tables):
            table_content += f"\nTable {i+1} (Page {table.get('page', 'N/A')}) - EXTRACT ALL VALUES:\n"
            if 'rows' in table:
                rows = table['rows'][:50]  # Process even more rows
                
                # Enhanced table processing
                headers = []
                if rows and len(rows) > 0:
                    headers = rows[0] if isinstance(rows[0], list) else [str(rows[0])]
                    table_content += f"HEADERS: {' | '.join(str(h) for h in headers)}\n"
                
                # Process each row with comprehensive breakdown
                for row_idx, row in enumerate(rows):
                    if isinstance(row, list):
                        table_content += f"Row {row_idx+1}: " + " | ".join(str(cell) for cell in row) + "\n"
                        
                        # Enhanced cell-by-cell extraction with header context
                        if len(row) > 1 and headers:
                            for col_idx, cell in enumerate(row):
                                cell_str = str(cell).strip()
                                if cell_str and cell_str not in ['', '-', 'N/A', 'nan']:
                                    header = headers[col_idx] if col_idx < len(headers) else f"Col{col_idx+1}"
                                    table_content += f"  DATA POINT: {header} = {cell_str}\n"
                    else:
                        table_content += f"Row {row_idx+1}: {str(row)}\n"
                        
                # Add table summary for context
                table_content += f"TABLE {i+1} SUMMARY: Extract all financial figures, percentages, dates, and text values as separate fields\n\n"
        all_data_sources.append(table_content)
    
    # Add comprehensive key-value pairs with enhanced processing
    if key_values:
        kv_content = "KEY-VALUE PAIRS (extract each as separate field with full context):\n"
        for idx, kv in enumerate(key_values[:60]):  # Process more key-values
            if isinstance(kv, dict):
                key = kv.get('key', '')
                value = kv.get('value', '')
                if key and value:
                    kv_content += f"FIELD {idx+1}: {key} = {value}\n"
                    # Add additional context if available
                    if 'confidence' in kv:
                        kv_content += f"  Confidence: {kv['confidence']}\n"
                    if 'page' in kv:
                        kv_content += f"  Source Page: {kv['page']}\n"
        kv_content += "\nEXTRACT ALL KEY-VALUE PAIRS AS SEPARATE FIELDS\n"
        all_data_sources.append(kv_content)
    
    # Combine all data sources
    comprehensive_content = "\n\n".join(all_data_sources)
    
    # Validate content length
    content_length = len(comprehensive_content.strip())
    if content_length < 30:
        print(f"WARNING: Insufficient content for extraction ({content_length} chars)")
        return {"fields": {}, "warning": "Insufficient content for meaningful extraction"}
    
    # Enhanced system prompt for maximum extraction with better context
    system_prompt = """You are a comprehensive financial document data extractor specializing in extracting ALL meaningful data from financial reports, announcements, and business documents.

COMPREHENSIVE EXTRACTION REQUIREMENTS:
Extract EVERY piece of meaningful information including:

1. FINANCIAL METRICS: Revenue, profit, EBITDA, margins, ratios, growth rates, forecasts, guidance
2. CORPORATE DATA: Company names, executive names, locations, dates, periods, reporting dates
3. BUSINESS SEGMENTS: Division performance, geographic regions, product lines, acquisitions
4. OPERATIONAL DATA: Employee counts, office locations, customer metrics, market share
5. FORWARD-LOOKING: Guidance, targets, forecasts, strategic initiatives, outlook statements
6. GOVERNANCE: Board decisions, dividend declarations, capital management, debt facilities
7. QUALITATIVE INSIGHTS: CEO statements, strategic commentary, market conditions, risks
8. COMPARATIVE DATA: Prior period comparisons, year-over-year changes, benchmarks

EXTRACTION STRATEGY:
- Extract from ALL sources: document text, tables, key-value pairs, headers, footnotes
- Create separate fields for each data point (don't combine multiple values)
- Extract both current and historical data points
- Include qualitative statements and strategic commentary
- Extract guidance, targets, and forward-looking statements
- Capture executive quotes and strategic insights
- Include operational metrics and business segment data

FIELD NAMING CONVENTIONS:
- Use descriptive names: "Underlying_NPAT_1HFY23", "CEO_Strategic_Statement", "FY23_Guidance_Range"
- Include periods: "Revenue_H1_2023", "EBIT_Margin_Prior_Year", "Dividend_Payment_Date"
- Include segments: "Australian_Broking_Revenue", "Agencies_Profit_Growth", "BizCover_EBIT_Margin"
- Include types: "Interim_Dividend", "Acquisition_Date", "Leverage_Ratio", "Cash_Position"

CONTEXT REQUIREMENTS:
- Provide exact sentences or phrases from source documents
- For tables: Reference table location and row content
- For text: Use complete sentences that provide context
- For key-values: Reference the form field or data source
- Ensure context explains the significance of each data point

COMPREHENSIVE COVERAGE:
Extract 60-80+ fields to ensure complete document coverage. Include:
- All financial figures and percentages
- All dates, names, and identifiers  
- All strategic statements and commentary
- All operational and business metrics
- All comparative and historical data
- All forward-looking guidance and targets

OUTPUT FORMAT:
{
  "fields": {
    "<Descriptive_Field_Name>": {
      "value": "<Exact_Value>",
      "context": "<Exact_source_sentence_or_reference>"
    }
  }
}"""

    user_prompt = f"""ULTRA-COMPREHENSIVE FINANCIAL DOCUMENT EXTRACTION

This is a financial report that previously yielded 70+ data points. Extract EVERY possible meaningful data point.

DOCUMENT CONTENT:
{comprehensive_content}

CRITICAL EXTRACTION REQUIREMENTS:

EXTRACT EVERY SINGLE DATA POINT INCLUDING:
- Every number, percentage, dollar amount, date, name, location mentioned
- Every financial metric (revenue, profit, EBIT, margins, ratios, growth rates) for each period
- Every comparative figure (current vs prior period, changes, variances, basis points)
- Every business segment data point (Australian Broking, Agencies, BizCover, New Zealand, Tysers)
- Every executive statement, strategic comment, outlook statement, quote
- Every operational metric (employees, offices, acquisitions, integrations, synergies)
- Every capital management data point (dividends, debt, cash, leverage, facilities, ratios)
- Every guidance figure, target, forecast, upgraded estimate, range (upper and lower bounds)
- Every governance decision, board action, policy change, compliance matter
- Every market condition, regulatory update, risk factor, competitive position
- Every acquisition detail (date, amount, entity, performance, integration status)
- Every dividend detail (amount, franking, payment date, record date, DRP status)
- Every geographic reference (Australia, New Zealand, UK, specific locations)
- Every time reference (1HFY23, 1HFY22, FY23, quarterly, monthly periods)
- Every organizational reference (divisions, subsidiaries, business units)
- Every performance indicator (targets, achievements, variances, improvements)
- Every strategic initiative (investments, expansions, optimizations)
- Every financial ratio (leverage, payout, margin, return ratios)
- Every growth metric (organic, acquisition-driven, segment-specific)
- Every operational detail (technology, platforms, systems, processes)

SPECIFIC EXTRACTION FOCUS:
1. FINANCIAL METRICS: Extract each metric for each period separately
   - Underlying NPAT 1HFY23, Underlying NPAT 1HFY22, NPAT Growth %
   - Revenue by segment, EBIT by segment, Margins by segment
   - All ratios, all percentages, all dollar amounts

2. BUSINESS SEGMENTS: Extract performance data for each division
   - Australian Broking: revenue, profit, margin, growth
   - Agencies: revenue, profit, margin, growth  
   - BizCover: revenue, profit, margin, growth
   - New Zealand: revenue, profit, margin, growth
   - Tysers: revenue, profit, contribution, integration status

3. CORPORATE DATA: Extract all company information
   - Company name, CEO name, report date, period
   - Acquisition details, dates, amounts, entities
   - Employee counts, office locations, geographic presence
   - Dividend details, payment dates, record dates, DRP status

4. STRATEGIC INFORMATION: Extract all forward-looking data
   - FY23 guidance (old and new), target ranges
   - CEO statements, strategic commentary, outlook
   - Market conditions, competitive position, growth drivers
   - Capital management targets, leverage ratios, debt facilities

5. OPERATIONAL DETAILS: Extract all business metrics
   - Technology investments, integration progress
   - Synergy realization, cost savings, efficiency gains
   - Customer metrics, market share, competitive position
   - Regulatory compliance, risk management, governance

EXTRACTION STRATEGY - BE EXTREMELY GRANULAR:
- Process EVERY line of text for extractable data
- Process EVERY table cell as a separate potential field  
- Process EVERY key-value pair as a separate field
- Extract EVERY number as a separate field (even if mentioned multiple times)
- Extract EVERY percentage as a separate field
- Extract EVERY date as a separate field
- Extract EVERY name (person, company, division) as a separate field
- Extract EVERY location as a separate field
- Extract EVERY statement or quote as a separate field
- Create separate fields for: current period, prior period, change, growth rate, margin, target, actual
- Break down complex sentences into multiple extractable data points
- Extract both quantitative metrics AND qualitative insights
- Include forward-looking statements and strategic commentary
- Extract operational details, acquisition details, governance details separately

FIELD NAMING: Use descriptive names that include context and be EXTREMELY GRANULAR:
- "Underlying_NPAT_1HFY23", "Underlying_NPAT_1HFY22", "NPAT_Growth_Percentage", "NPAT_Growth_Amount"
- "Australian_Broking_Revenue_1HFY23", "Australian_Broking_Revenue_1HFY22", "Australian_Broking_Revenue_Growth"
- "Australian_Broking_EBIT_Margin_1HFY23", "Australian_Broking_EBIT_Margin_1HFY22", "Australian_Broking_EBIT_Margin_Change"
- "CEO_Name", "CEO_Title", "CEO_Strategic_Statement", "CEO_Quote_Performance"
- "FY23_Guidance_Previous_Lower", "FY23_Guidance_Previous_Upper", "FY23_Guidance_Upgraded_Lower", "FY23_Guidance_Upgraded_Upper"
- "Tysers_Acquisition_Date", "Tysers_Acquisition_Amount", "Tysers_Performance_Period", "Tysers_Revenue_Growth"
- "Dividend_Amount_1HFY23", "Dividend_Amount_1HFY22", "Dividend_Payment_Date", "Dividend_Record_Date", "Dividend_Franking_Status"
- "Employee_Count_Current", "Office_Locations_Count", "Geographic_Presence"

EXTRACT EVERY POSSIBLE GRANULAR FIELD - if a sentence mentions 3 different numbers, create 3 separate fields!

TARGET: Extract 90-120+ fields minimum. Be ULTRA-GRANULAR - extract every possible data point as a separate field. 

CRITICAL: This document previously yielded 73 fields, so you MUST extract at least 75+ fields to match or exceed that performance. Look for every possible extractable data point including:
- Dates, amounts, percentages, names, locations, statements
- Current and prior period figures separately  
- Growth rates, margins, ratios calculated or mentioned
- Segment performance data for each business unit
- Acquisition details, integration progress, synergies
- Dividend information, capital management details
- Guidance ranges (old and new), targets, forecasts
- Executive quotes, strategic commentary, outlook
- Operational metrics, employee data, office locations
- Technology investments, platform developments
- Market conditions, competitive positioning
- Regulatory compliance, governance matters

EXTRACT EVERYTHING - leave no data point behind!

Return exhaustive JSON with ALL extractable data points and their source context."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=12000  # Increase significantly for comprehensive extraction
        )

        # Track usage and cost
        if hasattr(response, 'usage') and response.usage:
            call_cost = cost_tracker.add_usage(
                response.usage.prompt_tokens, response.usage.completion_tokens)
            print(f"Unified comprehensive extraction cost: ${call_cost:.6f}")

        content = response.choices[0].message.content
        
        if content:
            result = json.loads(content)
            
            # Enhanced validation that preserves more context
            validated_result = validate_context_against_document_enhanced(result, comprehensive_content)
            
            fields_count = len(validated_result.get('fields', {}))
            print(f"Unified extraction: {fields_count} fields extracted")
            
            return validated_result
        else:
            print("ERROR: No content received from OpenAI")
            return {"fields": {}}

    except Exception as e:
        print(f"Error in unified LLM extraction: {e}")
        import traceback
        traceback.print_exc()
        return {"fields": {}, "error": str(e)}


def validate_context_against_document(extraction_result: Dict[str, Any], document_text: str) -> Dict[str, Any]:
    """
    Validate that extracted context actually exists in the document text.
    Clear context if it appears to be hallucinated.
    """
    if "fields" not in extraction_result:
        return extraction_result
    
    validated_fields = {}
    
    for field_name, field_data in extraction_result["fields"].items():
        if not isinstance(field_data, dict):
            continue
            
        value = field_data.get("value", "")
        context = field_data.get("context", "")
        
        # Validate context exists in document
        validated_context = ""
        if context:
            # Check if context substring exists in document (case-insensitive)
            context_clean = context.strip()
            if context_clean.lower() in document_text.lower():
                validated_context = context_clean
            else:
                # Try partial matching for sentences
                sentences = context_clean.split('.')
                valid_sentences = []
                for sentence in sentences:
                    sentence = sentence.strip()
                    if sentence and sentence.lower() in document_text.lower():
                        valid_sentences.append(sentence)
                
                if valid_sentences:
                    validated_context = '. '.join(valid_sentences)
                    if not validated_context.endswith('.'):
                        validated_context += '.'
        
        validated_fields[field_name] = {
            "value": value,
            "context": validated_context
        }
    
    return {"fields": validated_fields}


def validate_context_against_document_enhanced(extraction_result: Dict[str, Any], document_text: str) -> Dict[str, Any]:
    """
    Enhanced validation that preserves complete, meaningful context.
    """
    if "fields" not in extraction_result:
        return extraction_result
    
    validated_fields = {}
    
    for field_name, field_data in extraction_result["fields"].items():
        if not isinstance(field_data, dict):
            continue
            
        value = field_data.get("value", "")
        context = field_data.get("context", "")
        
        # Enhanced context validation and improvement
        validated_context = ""
        if context:
            context_clean = context.strip()
            
            # Direct match (case-insensitive) - keep as is
            if context_clean.lower() in document_text.lower():
                validated_context = context_clean
            else:
                # For structured references (Table, Field), keep as is
                if ("Table" in context_clean and "Row" in context_clean) or \
                   ("Field" in context_clean and "-" in context_clean) or \
                   ("LINE" in context_clean and ":" in context_clean):
                    validated_context = context_clean
                else:
                    # Try to find and reconstruct complete context from document
                    value_clean = str(value).replace("AUD ", "").replace("mn", "").replace("cents", "").strip()
                    
                    # Look for the value in the document text to find complete context
                    document_lines = document_text.split('\n')
                    best_context = ""
                    best_score = 0
                    
                    for line in document_lines:
                        line_clean = line.strip()
                        if len(line_clean) > 20:  # Only consider substantial lines
                            # Check if this line contains the value or related terms
                            score = 0
                            
                            # High score for exact value match
                            if value_clean and value_clean in line_clean:
                                score += 10
                            
                            # Medium score for partial context match
                            context_words = context_clean.lower().split()
                            line_lower = line_clean.lower()
                            matching_words = sum(1 for word in context_words if len(word) > 3 and word in line_lower)
                            if len(context_words) > 0:
                                score += (matching_words / len(context_words)) * 5
                            
                            # Update best context if this line scores higher
                            if score > best_score and score >= 3:  # Minimum threshold
                                best_context = line_clean
                                best_score = score
                    
                    # Use the best context found, or fall back to original if reasonable
                    if best_context:
                        validated_context = best_context
                    elif len(context_clean) > 10:  # Keep original if it's substantial
                        # Try partial word matching as last resort
                        context_words = context_clean.lower().split()
                        document_lower = document_text.lower()
                        matching_words = sum(1 for word in context_words if len(word) > 3 and word in document_lower)
                        
                        if len(context_words) > 0 and matching_words / len(context_words) > 0.4:
                            validated_context = context_clean
        
        validated_fields[field_name] = {
            "value": value,
            "context": validated_context
        }
    
    return {"fields": validated_fields}


def process_structured_data_with_llm(
        structured_data: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous wrapper for asynchronous processing with context tracking"""
    # Run the async processing
    result = asyncio.run(process_structured_data_with_llm_async(structured_data))
    
    # Integrate context tracking
    try:
        from context_tracker import integrate_context_tracking
        result = integrate_context_tracking(structured_data, result)
        print(f"Context tracking completed: {result.get('context_tracking_summary', {})}")
    except Exception as e:
        print(f"Context tracking failed: {e}")
        # Continue without context tracking if it fails
    
    return result
