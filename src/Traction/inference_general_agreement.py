"""
Script: Zero-shot general (cross-sector) agreement inference between IMF staff and country authority.

Ports the prompt and output semantics of `temp/reference_code/9.llm_general.py` onto
the production Batch API + Pydantic-schema infrastructure used by
`inference_agreement_stance.py`. Consumes a document-level CSV (default:
`df_documents.csv`; the incremental shell wrapper passes
`df_documents_incremental.csv`) whose columns already match the
`TASK_COLUMN_MAPPINGS['agreement']` placeholders (`staff`, `buff`, `country`,
`year`) — no pivoting needed.
"""

#%%
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))
from dotenv import load_dotenv
load_dotenv(_REPO_ROOT / '.env')

import pandas as pd

from prompts.schema import PROMPT_REGISTRY
from prompts.prompt_examples import TASK_COLUMN_MAPPINGS
from inference_agreement_stance import (
    _add_common_cli,
    _build_and_optionally_submit,
    _post_process_if_needed,
)

ID_COL = 'Print ISBN'
STAFF_COL = 'staff'
AUTHORITY_COL = 'buff'


def parse_args(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description='General (cross-sector) zero-shot agreement inference (OpenAI Batch)')
    _add_common_cli(parser)
    parser.add_argument('--max-input-length', type=int, default=20000)
    parser.add_argument(
        '--output-file',
        type=str,
        default='df_documents_general.csv',
        help="Output CSV filename (resolved relative to --output-dir). "
             "Use 'df_documents_general_incremental.csv' for incremental runs.",
    )
    # Override the defaults from `_add_common_cli` that target stance/agreement runs.
    parser.set_defaults(
        data_file='/data/home/xiong/data/Fund/CSR/Tractions/output/df_documents.csv',
        model='gpt-5.4-mini',
        prompt_variant='simple',
        max_output_tokens=16384,
    )
    return parser.parse_args(argv)


#%%
def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    results_dir = Path(args.output_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.data_file)
    print(f"Loaded {len(df)} rows from {args.data_file}")

    # Drop rows missing either side of the bilateral comparison — the prompt
    # is meaningless without both staff and authority text.
    before = len(df)
    df = df[df[STAFF_COL].notna() & df[AUTHORITY_COL].notna()].copy()
    df = df[df[STAFF_COL].astype(str).str.strip().ne('') & df[AUTHORITY_COL].astype(str).str.strip().ne('')]
    dropped = before - len(df)
    if dropped:
        print(f"Dropped {dropped} rows missing staff or buff text; {len(df)} rows remain")

    if args.test_mode:
        df = df.sample(n=min(args.sample_size, len(df)), random_state=42)
        print(f"Test mode: sampled {len(df)} rows")

    df = df.reset_index(drop=True)
    df['id'] = df.index.astype(str)

    prompt_key = f"general_agreement_{args.prompt_variant}"
    if prompt_key not in PROMPT_REGISTRY:
        raise ValueError(f"Prompt key '{prompt_key}' not in PROMPT_REGISTRY")
    response_model = PROMPT_REGISTRY[prompt_key]['response_model']

    # Reuse the existing agreement column mapping — df_documents schema lines up 1:1.
    column_mapping = TASK_COLUMN_MAPPINGS['agreement'].copy()

    jsonl_path = results_dir / (args.jsonl_file or "general_agreement_batch.jsonl")
    _, results_jsonl_path = _build_and_optionally_submit(
        df,
        prompt_key=prompt_key,
        response_model=response_model,
        column_mapping=column_mapping,
        jsonl_path=jsonl_path,
        args=args,
    )
    _post_process_if_needed(
        df,
        args=args,
        results_jsonl_path=results_jsonl_path,
        out_csv_path=results_dir / args.output_file,
    )


if __name__ == "__main__":
    main()
