## topic_identification with batch processing

#%%
import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple

sys.path.insert(0, str('../../'))
from dotenv import load_dotenv
load_dotenv('../../.env')

import pandas as pd
from openai import OpenAI
from openai.lib._parsing._completions import type_to_response_format_param
from pydantic import BaseModel
from typing import Type
 
from libs.prompt_utils import load_prompt
from prompts.schema import TopicResponse
from llm_batch_process_utils import _build_batch_messages_from_df
from topic_identification import _convert_response_to_wide_df

#%%

def create_batch_jsonl(
    df: pd.DataFrame,
    prompt_sections: Dict[str, str],
    output_jsonl_path: Path,
    *,
    model: str,
    temperature: float,
    max_input_text_length: int = 2000,
    endpoint: str = '/v1/chat/completions',
    response_model: Type[BaseModel] = None,
) -> List[str]:
    """Create a JSONL file for OpenAI Batch with structured output.

    Each line contains one HTTP request descriptor with a custom_id matching the
    source row id so we can merge results later.
    """

    # Reuse existing helper to build messages and ids in the same way
    batch_messages, batch_ids = _build_batch_messages_from_df(
        df,
        prompt_sections,
        text_column='text',
        id_column='id',
        max_input_text_length=max_input_text_length,
    )
    # Ensure directory exists
    output_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    if response_model:
        response_format = type_to_response_format_param(response_model)

    with open(output_jsonl_path, 'w', encoding='utf-8') as f:
        for msg_id, messages in zip(batch_ids, batch_messages):
            body: Dict[str, Any]
            if endpoint == '/v1/chat/completions':
                body = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "response_format": response_format,
                }
            else:  # '/v1/responses' uses the Responses API format
                body = {
                    "model": model,
                    "input": messages,  # Responses API accepts messages as input
                    "temperature": temperature,
                    "response_format": response_format,
                }

            request_obj = {
                "custom_id": str(msg_id),
                "method": "POST",
                "url": endpoint,
                "body": body,
            }
            f.write(json.dumps(request_obj, ensure_ascii=False) + "\n")

    return batch_ids


def upload_file_and_create_batch(client: OpenAI, jsonl_path: Path, endpoint: str = '/v1/chat/completions') -> Dict[str, Any]:
    """Upload JSONL as a file and create an OpenAI Batch job."""
    file_obj = client.files.create(file=open(jsonl_path, 'rb'), purpose='batch')
    batch = client.batches.create(input_file_id=file_obj.id, endpoint=endpoint, completion_window='24h')
    return {"file": file_obj, "batch": batch}
        
def wait_for_batch_completion(client, batch_id: str, poll_seconds: int = 5, one_line: bool = True):
    term = {"completed", "failed", "expired", "canceled"}

    def to_map(x):
        if not x: return {}
        if isinstance(x, dict): return x
        for m in ("model_dump", "to_dict", "dict"):
            f = getattr(x, m, None)
            if callable(f):
                try: return dict(f())
                except: pass
        d = getattr(x, "__dict__", {})
        return d if isinstance(d, dict) else {}

    while True:
        b = client.batches.retrieve(batch_id)
        status = getattr(b, "status", None) or (b.get("status") if isinstance(b, dict) else None)
        rc = to_map(getattr(b, "request_counts", None) or (b.get("request_counts") if isinstance(b, dict) else None))

        s = (rc.get("succeeded", None) if rc.get("succeeded", None) is not None else rc.get("completed", 0)) or 0
        f = rc.get("failed", 0) or 0
        c = rc.get("canceled", 0) or 0
        total = rc.get("total") or max(rc.get("submitted", 0), s + f + c, rc.get("in_progress", 0)) or 0
        done = s + f + c
        pct = (done / total * 100) if total else 0

        line = f"Batch {batch_id} status: {status}"
        if rc: line += f" | progress: {done}/{total} ({pct:.1f}%) [succeeded={s}, failed={f}, canceled={c}]"

        if one_line:
            sys.stdout.write("\r" + line.ljust(140)); sys.stdout.flush()
        else:
            print(line, flush=True)

        if status in term:
            if one_line: sys.stdout.write("\n"); sys.stdout.flush()
            return b

        time.sleep(poll_seconds)

def download_batch_results(client: OpenAI, batch_obj: Dict[str, Any], output_path: Path) -> Path:
    """Download results JSONL for a completed batch."""
    # Handle potential SDK object fields vs dicts
    output_file_id = getattr(batch_obj, 'output_file_id', None) or getattr(batch_obj, 'output_file_ids', None)
    if isinstance(output_file_id, list):
        output_file_id = output_file_id[0] if output_file_id else None
    if not output_file_id and isinstance(batch_obj, dict):
        output_file_id = batch_obj.get('output_file_id') or (
            (batch_obj.get('output_file_ids') or [None])[0]
        )
    if not output_file_id:
        raise RuntimeError("Batch completed but no output_file_id was found")

    content = client.files.content(output_file_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'wb') as f:
        f.write(content.content)
    return output_path

def _try_parse_topic_response_from_text(text: str) -> Dict[str, Any]:
    """Attempt to parse a TopicResponse-compatible dict from model text output."""
    # Strip code fences if present
    cleaned = text.strip()
    cleaned = cleaned.replace("```json\n", "").replace("```\n", "").replace("```", "")
    try:
        data = json.loads(cleaned)
        # Validate via Pydantic if possible
        try:
            model = TopicResponse.model_validate(data)  # pydantic v2
        except Exception:
            model = TopicResponse.parse_obj(data)  # pydantic v1 fallback
        return model.dict()
    except Exception:
        # Return a sentinel error structure; caller can log/inspect later
        return {"error": cleaned}


def post_process_results_jsonl(results_jsonl_path: Path) -> List[Dict[str, Any]]:
    """Parse batch results JSONL and return list of records with 'id' and TopicResponse fields."""
    merged_results: List[Dict[str, Any]] = []
    with open(results_jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)

            # Obtain custom_id and response body depending on shape
            custom_id = obj.get('custom_id') or obj.get('id')
            body = None
            if 'response' in obj and isinstance(obj['response'], dict):
                body = obj['response'].get('body')
            elif 'result' in obj and isinstance(obj['result'], dict):
                body = obj['result']

            record: Dict[str, Any] = {"id": str(custom_id) if custom_id is not None else None}

            if body is None:
                record["error"] = obj
                merged_results.append(record)
                continue

            # Chat Completions style
            if 'choices' in body:
                try:
                    message = body['choices'][0]['message']
                    content = message.get('content')
                    if content is None and 'parsed' in message:
                        # Rare: SDK-like parsed in batch
                        parsed_model = message['parsed']
                        if isinstance(parsed_model, dict):
                            record.update(parsed_model)
                        else:
                            record["error"] = message
                    else:
                        record.update(_try_parse_topic_response_from_text(content))
                except Exception as e:
                    record["error"] = f"parse_error: {e}"
            # Responses API style
            elif 'output' in body:
                try:
                    # output could be a list of content blocks
                    outputs = body.get('output', []) or []
                    # Find the first text block
                    text_parts = []
                    for block in outputs:
                        if isinstance(block, dict) and block.get('type') == 'message':
                            for item in block.get('content', []) or []:
                                if item.get('type') == 'output_text' and 'text' in item:
                                    text_parts.append(item['text'])
                    content = "\n".join(text_parts)
                    record.update(_try_parse_topic_response_from_text(content))
                except Exception as e:
                    record["error"] = f"parse_error: {e}"
            else:
                record["error"] = body

            merged_results.append(record)

    return merged_results
#%%
def parse_args(argv=None):
    """Parse command line arguments for batch topic identification"""
    import argparse

    parser = argparse.ArgumentParser(description='LLM Topic Identification (OpenAI Batch)')
    parser.add_argument('--test-mode', action='store_true', default=False,
                        help='Run in test mode with sample data (default: False)')
    parser.add_argument('--sample-size', type=int, default=1000,
                        help='Sample size for test mode (default: 1000)')
    parser.add_argument('--data-dir', type=str,
                        default='/data/home/xiong/data/Fund/CSR/Tractions/',
                        help='Data directory path')
    parser.add_argument('--output-dir', type=str,
                        default='/data/home/xiong/data/Fund/CSR/Tractions/output',
                        help='Output directory path')
    parser.add_argument('--input_file', type=str, default='df_paragraphs.csv',
                        help='Input file name')
    parser.add_argument('--prompt-file', type=str, default='./prompts/topic_classification.md',
                        help='Prompt file name')
    parser.add_argument('--output_file', type=str, default='paragraph_with_sector_batch.csv',
                        help='Post-processed CSV output file name')
    parser.add_argument('--model', type=str, default='gpt-5-nano',
                        help='OpenAI model to use (default: gpt-5-nano)')
    parser.add_argument('--temperature', type=float, default=1.0,
                        help='Model temperature (default: 1.0) for GPT-5-nano')
    parser.add_argument('--max-input-length', type=int, default=2000,
                        help='Maximum input text length (default: 2000)')
    parser.add_argument('--endpoint', type=str, default='/v1/chat/completions',
                        choices=['/v1/chat/completions', '/v1/responses'],
                        help='OpenAI batch endpoint to target')
    parser.add_argument('--jsonl-file', type=str, default='topic_identification_batch.jsonl',
                        help='Filename for the generated batch JSONL requests file')
    parser.add_argument('--submit', action='store_true', default=False,
                        help='If set, upload the JSONL, create the batch and wait for completion')
    parser.add_argument('--create-batch', action='store_true', default=False,
                        help='If set, create the batch jsonl file')
    parser.add_argument('--post-process', action='store_true', default=False,
                        help='If set, post-process the results JSONL')
    parser.add_argument('--results-jsonl', type=str, default=None,
                        help='Optional: existing results JSONL to post-process (skips submit)')
    return parser.parse_args(argv)

#%%
if __name__ == "__main__":
    args = parse_args(['--test-mode', '--sample-size', '1000','--create-batch','--submit','--post-process'])
    print(args)
    data_dir = Path(args.data_dir)
    results_dir = Path(args.output_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = args.prompt_file

    # Load data
    df_paragraphs = pd.read_csv(results_dir / args.input_file)
    df_paragraphs = df_paragraphs[df_paragraphs['text'].notna()].copy()
    df_paragraphs['id'] = df_paragraphs.index.astype(str)
    if args.test_mode:
        df_paragraphs = df_paragraphs.sample(n=min(args.sample_size, len(df_paragraphs)), random_state=42)

    # Load prompt sections
    prompt_sections = load_prompt(prompt_path).sections

    # 1) Create batch JSONL
    jsonl_path = results_dir / args.jsonl_file
    if args.create_batch:
        ids = create_batch_jsonl(
            df_paragraphs,
            prompt_sections,
            jsonl_path,
            model=args.model,
            temperature=args.temperature,
            max_input_text_length=args.max_input_length,
            endpoint=args.endpoint,
            response_model=TopicResponse,
        )
        print(f"Wrote {len(ids)} requests to {jsonl_path}")

    results_jsonl_path: Path | None = None

    # 2) Upload and retrieve results (optional via --submit)
    if args.submit:
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OPENAI_API_KEY is not set; please set it in .env file")
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        created = upload_file_and_create_batch(client, jsonl_path, endpoint=args.endpoint)
        batch_id = created['batch'].id if hasattr(created['batch'], 'id') else created['batch']['id']
        print(f"Created batch: {batch_id}")
        final_batch = wait_for_batch_completion(client, batch_id, poll_seconds=5, one_line=True)
        ts = int(time.time())
        results_jsonl_path = results_dir / f"batch_results_{batch_id}_{ts}.jsonl"
        download_batch_results(client, final_batch, results_jsonl_path)
        print(f"Downloaded results to {results_jsonl_path}")

    # 3) Post-process results (if we have a results JSONL)
    if args.post_process:
        if args.results_jsonl:
            results_jsonl_path = Path(args.results_jsonl)
        if results_jsonl_path and results_jsonl_path.exists():
            merged_results = post_process_results_jsonl(results_jsonl_path)
            print(f"Parsed {len(merged_results)} results from {results_jsonl_path}")

            # Convert to wide format and merge back to original
            df_wide = _convert_response_to_wide_df(merged_results)
            merged_df = df_paragraphs.merge(df_wide, on='id', how='left')

            # Create dummy columns where confidence > 30
            topic_columns = [col for col in df_wide.columns if col != 'id']
            for col in topic_columns:
                merged_df[f"{col}_dummy"] = (merged_df[col] > 30).astype(int)

            # Save final CSV
            output_file_path = results_dir / args.output_file
            merged_df.to_csv(output_file_path, index=False)
            print(f"Output saved to {output_file_path}")
        else:
            print("No results JSONL provided or created. Skipping post-processing.")

