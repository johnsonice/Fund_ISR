"""
Script: Inference for agreement and stance between IMF staff and country authority.

Implements two tasks using OpenAI Batch API with existing utilities:
1) Agreement (monetary or fiscal): reshapes rows to have staff and authority texts side-by-side.
2) Stance (monetary or fiscal): per-row stance classification for a single author (staff/authority).

Follows batching structure similar to `topic_identification_batch.py` and prompt/message
construction per `notebooks/Traction/evaluate_fiscal_monetray_prompts.ipynb`.
"""

#%%
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Ensure repo root is on sys.path regardless of current working directory.
# This script lives at: <repo_root>/src/Traction/inference_agreement_stance.py
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))
from dotenv import load_dotenv
load_dotenv(_REPO_ROOT / '.env')

import pandas as pd
from openai import OpenAI
from openai.lib._parsing._completions import type_to_response_format_param
from pydantic import BaseModel
from typing import Type

from libs.prompt_utils import load_prompt
from llm_batch_process_utils import _build_batch_messages_from_df, _build_batch_messages_from_df_flexible
from prompts.schema import (
    PROMPT_REGISTRY,
    MonetaryAgreementResponse,
    FiscalAgreementResponse,
    MonetaryStanceResponse,
    FiscalStanceResponse,
)
from prompts.prompt_examples import (
    AUTHOR_TYPE_MAPPING,
    AUTHOR_TYPE_POSSESSIVE_MAPPING,
    AUTHOR_VERB_MAPPING,
    TASK_EXAMPLES,
    TASK_EXPLANATIONS,
    TASK_COLUMN_MAPPINGS
)
from topic_identification_batch import (
    upload_file_and_create_batch,
    wait_for_batch_completion,
    download_batch_results,
)

# Expected column names in input CSV (matches TASK_COLUMN_MAPPINGS)
STAFF_COL = 'staff'
AUTHORITY_COL = 'buff'
TOPIC_COL = 'topic'
TYPE_COL = 'type'  # Column indicating staff/buff
TEXT_COL = 'text'
COUNTRY_COL = 'country'
YEAR_COL = 'year'
ID_COL = 'Print ISBN'


#%%
def _pivot_agreement_rows(df: pd.DataFrame, *, id_cols: List[str], type_col: str, text_col: str) -> pd.DataFrame:
    """Pivot long rows (types staff/buff) into wide with staff/authority columns.

    Expects `type_col` values to include 'staff' and 'buff' (authority).
    Keeps unique keys by `id_cols` and `topic` if present among id_cols.
    """
    if not set([type_col, text_col]).issubset(df.columns):
        missing = [c for c in [type_col, text_col] if c not in df.columns]
        raise ValueError(f"Missing required columns: {missing}")

    # Normalize type names
    df = df.copy()
    df[type_col] = df[type_col].str.strip().str.lower()
    # Pivot using original role labels ('staff' and 'buff') without renaming
    role_col = type_col
    wide = df.pivot_table(index=id_cols, 
                          columns=role_col, 
                          values=text_col, 
                          aggfunc=lambda x: ' '.join(x))
    wide = wide.reset_index()
    # Ensure expected columns exist
    for col in [STAFF_COL, AUTHORITY_COL]:
        if col not in wide.columns:
            wide[col] = None
    return wide
#%%

def _create_batch_jsonl(
    df: pd.DataFrame,
    prompt_sections: Dict[str, str],
    output_jsonl_path: Path,
    *,
    model: str,
    temperature: float,
    endpoint: str,
    response_model: Type[BaseModel],
    message_builder: str,
    builder_kwargs: Dict[str, Any],
    max_output_tokens: int = 8000,
) -> List[str]:
    """Create a JSONL file compatible with OpenAI Batch requests.

    message_builder: 'simple' uses `_build_batch_messages_from_df`,
                     'flexible' uses `_build_batch_messages_from_df_flexible`.
    builder_kwargs: arguments passed to the selected message builder.
    """
    if message_builder == 'simple':
        batch_messages, batch_ids = _build_batch_messages_from_df(df, prompt_sections, **builder_kwargs)
    elif message_builder == 'flexible':
        batch_messages, batch_ids = _build_batch_messages_from_df_flexible(df, prompt_sections, **builder_kwargs)
    else:
        raise ValueError("message_builder must be 'simple' or 'flexible'")

    output_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    response_format = type_to_response_format_param(response_model) if response_model else None

    with open(output_jsonl_path, 'w', encoding='utf-8') as f:
        for msg_id, messages in zip(batch_ids, batch_messages):
            if endpoint == '/v1/chat/completions':
                body = {"model": model, "messages": messages, "temperature": temperature, "response_format": response_format, "max_completion_tokens": max_output_tokens}
            else:
                body = {"model": model, "input": messages, "temperature": temperature, "response_format": response_format, "max_output_tokens": max_output_tokens}
            request_obj = {"custom_id": str(msg_id), "method": "POST", "url": endpoint, "body": body}
            f.write(json.dumps(request_obj, ensure_ascii=False) + "\n")

    return batch_ids

## Reuse upload/wait/download from topic_identification_batch
def _parse_structured_result(text: str) -> Dict[str, Any]:
    cleaned = (text or "").strip().replace("```json\n", "").replace("````\n", "").replace("```", "")
    try:
        return json.loads(cleaned)
    except Exception:
        return {"error": cleaned}

def _post_process_results_jsonl(results_jsonl_path: Path) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    with open(results_jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            custom_id = obj.get('custom_id') or obj.get('id')
            body = None
            if 'response' in obj and isinstance(obj['response'], dict):
                body = obj['response'].get('body')
            elif 'result' in obj and isinstance(obj['result'], dict):
                body = obj['result']

            record: Dict[str, Any] = {"id": str(custom_id) if custom_id is not None else None}
            if not body:
                record["error"] = obj
                merged.append(record)
                continue
            if 'choices' in body:
                try:
                    message = body['choices'][0]['message']
                    content = message.get('content')
                    if content is not None:
                        record.update(_parse_structured_result(content))
                    else:
                        parsed = message.get('parsed')
                        if isinstance(parsed, dict):
                            record.update(parsed)
                        else:
                            record['error'] = message
                except Exception as e:
                    record['error'] = f"parse_error: {e}"
            elif 'output' in body:
                try:
                    outputs = body.get('output', []) or []
                    text_parts = []
                    for block in outputs:
                        if isinstance(block, dict) and block.get('type') == 'message':
                            for item in block.get('content', []) or []:
                                if item.get('type') == 'output_text' and 'text' in item:
                                    text_parts.append(item['text'])
                    content = "\n".join(text_parts)
                    record.update(_parse_structured_result(content))
                except Exception as e:
                    record['error'] = f"parse_error: {e}"
            else:
                record['error'] = body
            merged.append(record)
    return merged
#%%

def _select_prompt_and_response(task: str, domain: str, prompt_variant: str = 'few_shot') -> Tuple[str, Type[BaseModel]]:
    """Return (prompt_key, response_model) based on task, domain, and prompt variant."""
    if task not in ('agreement', 'stance'):
        raise ValueError(f"Unknown task: {task}")
    if domain not in ('monetary', 'fiscal'):
        raise ValueError(f"Unknown domain: {domain}")

    prompt_key = f"{domain}_{task}_{prompt_variant}"

    # Look up the prompt in PROMPT_REGISTRY (already imported from schema.py)
    if prompt_key not in PROMPT_REGISTRY:
        raise ValueError(f"Prompt key '{prompt_key}' not found in PROMPT_REGISTRY")

    # Get the response model from the registry
    response_model = PROMPT_REGISTRY[prompt_key].get('response_model')
    if response_model is None:
        raise ValueError(f"No response model found for prompt key '{prompt_key}'")

    return prompt_key, response_model


def _build_and_optionally_submit(
    df_payload: pd.DataFrame,
    *,
    prompt_key: str,
    response_model: Type[BaseModel],
    column_mapping: Dict[str, str],
    jsonl_path: Path,
    args,
    id_column: str = 'id',
) -> Tuple[List[str], Path | None]:
    """Create batch JSONL, optionally submit, and return (ids, results_jsonl_path)."""
    prompt_meta = PROMPT_REGISTRY[prompt_key]
    prompt_path = Path(__file__).parent / 'prompts' / prompt_meta['prompt_file']
    prompt_sections = load_prompt(prompt_path).sections

    ids = _create_batch_jsonl(
        df_payload,
        prompt_sections,
        jsonl_path,
        model=args.model,
        temperature=args.temperature,
        endpoint=args.endpoint,
        response_model=response_model,
        message_builder='flexible',
        builder_kwargs={
            'column_mapping': column_mapping,
            'id_column': id_column,
            'max_text_length': args.max_input_length,
        },
        max_output_tokens=args.max_output_tokens,
    )
    print(f"Wrote {len(ids)} requests to {jsonl_path}")

    results_jsonl_path: Path | None = None
    if args.submit:
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OPENAI_API_KEY is not set; please set it in .env file")
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        print(f"Submitting batch with model={args.model}, endpoint={args.endpoint}, prompt_key={prompt_key}")
        created = upload_file_and_create_batch(client, jsonl_path, endpoint=args.endpoint)
        batch_id = created['batch'].id if hasattr(created['batch'], 'id') else created['batch']['id']
        print(f"Created batch: {batch_id}")
        final_batch = wait_for_batch_completion(client, batch_id, poll_seconds=30)
        ts = int(time.time())
        results_jsonl_path = jsonl_path.parent / f"batch_results_{batch_id}_{ts}.jsonl"
        download_batch_results(client, final_batch, results_jsonl_path)
        print(f"Downloaded results to {results_jsonl_path}")

    return ids, results_jsonl_path


def _post_process_if_needed(base_df: pd.DataFrame, *, args, results_jsonl_path: Path | None, out_csv_path: Path) -> None:
    if args.post_process:
        if args.results_jsonl:
            results_jsonl_path = Path(args.results_jsonl)
        if results_jsonl_path and results_jsonl_path.exists():
            merged_results = _post_process_results_jsonl(results_jsonl_path)
            df_out = base_df.merge(pd.DataFrame(merged_results), on='id', how='left')
            df_out.to_csv(out_csv_path, index=False)
            print(f"Output saved to {out_csv_path}")
        else:
            print("No results JSONL provided or created. Skipping post-processing.")


def _filter_domain(df: pd.DataFrame, domain: str, topic_col: str = TOPIC_COL) -> pd.DataFrame:
    """Filter by domain if topic column exists; otherwise return df unchanged."""
    if topic_col in df.columns:
        dom = 'monetary' if domain == 'monetary' else 'fiscal'
        return df[df[topic_col].str.contains(dom, case=False, na=False)].copy()
    return df


def _add_common_cli(parser):
    parser.add_argument('--test-mode', action='store_true', default=False)
    parser.add_argument('--sample-size', type=int, default=1000)
    parser.add_argument('--data-file', type=str, default='/data/home/xiong/data/Fund/CSR/Tractions/output/document_by_type_sector.csv')
    parser.add_argument('--output-dir', type=str, default='/data/home/xiong/data/Fund/CSR/Tractions/output')
    parser.add_argument('--model', type=str, default='gpt-5-nano')
    parser.add_argument('--temperature', type=float, default=1.0)
    parser.add_argument('--endpoint', type=str, default='/v1/chat/completions', choices=['/v1/chat/completions', '/v1/responses'])
    parser.add_argument('--jsonl-file', type=str, default=None)
    parser.add_argument('--submit', action='store_true', default=False)
    parser.add_argument('--post-process', action='store_true', default=False)
    parser.add_argument('--results-jsonl', type=str, default=None)
    parser.add_argument('--prompt-variant', type=str, default='few_shot', help="Prompt key suffix; expects PROMPT_REGISTRY key pattern {domain}_{task}_{variant}")
    parser.add_argument('--max-output-tokens', type=int, default=8000, help='Maximum tokens for model output (default: 2000)')
    return parser


def parse_args(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description='Agreement and Stance Inference (OpenAI Batch)')
    sub = parser.add_subparsers(dest='task', required=False)

    # Agreement task
    p_agree = sub.add_parser('agreement', help='Infer agreement between staff and authority')
    _add_common_cli(p_agree)
    p_agree.add_argument('--domain', type=str, choices=['monetary', 'fiscal'], required=False, default='monetary')
    p_agree.add_argument('--max-input-length', type=int, default=20000)

    # Stance task
    p_stance = sub.add_parser('stance', help='Infer stance for each row')
    _add_common_cli(p_stance)
    p_stance.add_argument('--domain', type=str, choices=['monetary', 'fiscal'], required=True,default='monetary')
    p_stance.add_argument('--max-input-length', type=int, default=20000)

    # Default to agreement task in interactive/no-args mode and when subcommand omitted
    parser.set_defaults(task='agreement')

    if argv == [] or argv is None:
        return parser.parse_args(['agreement'])
    tokens = list(argv)
    if len(tokens) == 0:
        tokens = ['agreement']
    elif tokens[0] not in ('agreement', 'stance'):
        tokens = ['agreement'] + tokens

    return parser.parse_args(tokens)

#%%
def main(argv=None):
    # Honor real CLI args when called from the shell; fall back to provided argv for programmatic use
    args = parse_args(sys.argv[1:] if argv is None else argv)
    #args = parse_args(sys.argv[1:] if argv is None else [])
    results_dir = Path(args.output_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(args.data_file)
    if args.test_mode:
        # keep only non-null text and sample
        if TEXT_COL in df.columns:
            df = df[df[TEXT_COL].notna()].copy()
        df = df.sample(n=min(args.sample_size, len(df)), random_state=42)

    if args.task == 'agreement':
        print(args)
        df = _filter_domain(df, args.domain, TOPIC_COL)

        id_cols = [c for c in [ID_COL, TOPIC_COL, COUNTRY_COL, YEAR_COL] if c in df.columns]
        wide = _pivot_agreement_rows(df, id_cols=id_cols, type_col=TYPE_COL, text_col=TEXT_COL)
        wide = wide.reset_index(drop=True)
        wide['id'] = wide.index.astype(str)

        prompt_key, response_model = _select_prompt_and_response('agreement', args.domain, args.prompt_variant)

        # Use centralized column mapping from prompt_examples
        column_mapping = TASK_COLUMN_MAPPINGS['agreement'].copy()

        jsonl_path = results_dir / (args.jsonl_file or f"agreement_{args.domain}_batch.jsonl")
        _, results_jsonl_path = _build_and_optionally_submit(
            wide,
            prompt_key=prompt_key,
            response_model=response_model,
            column_mapping=column_mapping,
            jsonl_path=jsonl_path,
            args=args,
        )
        _post_process_if_needed(wide, args=args, results_jsonl_path=results_jsonl_path, out_csv_path=results_dir / f"agreement_{args.domain}_results.csv")

    elif args.task == 'stance':
        print(args)
        # Domain filter if column exists
        df = _filter_domain(df, args.domain, TOPIC_COL)

        # Stance is a per-text classification for BOTH monetary and fiscal prompts.
        # (Fiscal prompts also use a single {TEXT} field; they do not require pivoting staff/buff into wide rows.)
        keep_cols = [
            c
            for c in [
                ID_COL,
                TOPIC_COL if TOPIC_COL in df.columns else None,
                COUNTRY_COL,
                YEAR_COL,
                TYPE_COL,
                TEXT_COL,
            ]
            if c and c in df.columns
        ]
        df_s = df[keep_cols].copy()
        # Normalize author column
        if TYPE_COL in df_s.columns:
            df_s[TYPE_COL] = df_s[TYPE_COL].astype(str).str.strip().str.lower()

        # Get task-specific examples and explanations from centralized constants
        task_type = f"{args.domain}_stance"
        example_dict = TASK_EXAMPLES.get(task_type, {})
        explanation_dict = TASK_EXPLANATIONS.get(task_type, {})

        # Populate prompt-format fields using centralized mappings
        type_series = df_s[TYPE_COL] if TYPE_COL in df_s.columns else pd.Series([""] * len(df_s))
        df_s['author_type'] = type_series.map(AUTHOR_TYPE_MAPPING).fillna(type_series.astype(str))
        df_s['type_possessive'] = type_series.map(AUTHOR_TYPE_POSSESSIVE_MAPPING).fillna(type_series.astype(str))
        df_s['verb'] = type_series.map(AUTHOR_VERB_MAPPING).fillna('stated')
        df_s['examples'] = type_series.map(example_dict).fillna('')
        df_s['explanation'] = type_series.map(explanation_dict).fillna('')


        # Basic cleaning
        df_s = df_s[df_s[TEXT_COL].notna()].copy()
        df_s[TEXT_COL] = df_s[TEXT_COL].astype(str).str.strip()
        df_s = df_s.reset_index(drop=True)
        df_s["id"] = df_s.index.astype(str)

        prompt_key, response_model = _select_prompt_and_response("stance", args.domain, args.prompt_variant)

        # Use centralized column mapping from prompt_examples
        column_mapping = TASK_COLUMN_MAPPINGS['stance'].copy()

        jsonl_path = results_dir / (args.jsonl_file or f"stance_{args.domain}_batch.jsonl")
        _, results_jsonl_path = _build_and_optionally_submit(
            df_s,
            prompt_key=prompt_key,
            response_model=response_model,
            column_mapping=column_mapping,
            jsonl_path=jsonl_path,
            args=args,
        )
        _post_process_if_needed(
            df_s,
            args=args,
            results_jsonl_path=results_jsonl_path,
            out_csv_path=results_dir / f"stance_{args.domain}_results.csv",
        )

    else:
        raise ValueError('Unknown task')


if __name__ == "__main__":
    main()
