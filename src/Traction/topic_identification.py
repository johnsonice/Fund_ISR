#### LLM topic identification
#%%
from ast import Dict
import os, sys
from typing import Any
sys.path.insert(0, str('../../'))
from dotenv import load_dotenv
load_dotenv('../../.env') ## load api key from .env file

from pathlib import Path
import pandas as pd  # keep original usage
import asyncio
from typing import List, Dict, Any

from llm_batch_process_utils import _build_batch_messages_from_df, _process_batch_async, _merge_ids_with_responses
from prompts.schema import TopicResponse
from libs.prompt_utils import load_prompt
from libs.llm_factory_openai import BatchAsyncLLMAgent

import warnings
warnings.filterwarnings("ignore")
#%%

def _convert_response_to_wide_df(merged_results: List[Dict[str, Any]]) -> pd.DataFrame:
    # Step 1: flatten out topic_labels so each (id, topic, confidence) is a row
    rows = []
    for item in merged_results:
        for t in item["topic_labels"]:
            rows.append({"id": item["id"], "topic": t["topic"], "confidence": t["confidence"]})
    df_long = pd.DataFrame(rows)
    # Step 2: pivot to wide format
    df = df_long.pivot(index="id", columns="topic", values="confidence").reset_index()
    df = df.fillna(0)
    # Fill missing columns with 0 if they don't exist
    expected_columns = ["id","Economic Outlook","Monetary Policy","Fiscal Stance",
        "Financial Stability", "External Stance","Other"]
    for col in expected_columns:
        if col not in df.columns:
            df[col] = 0
    # Reorder columns to match expected order
    df = df[expected_columns]
    return df

def parse_args(argv=None):
    """Parse command line arguments for topic identification"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LLM Topic Identification')
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
    parser.add_argument('--output_file', type=str, default='paragraph_with_sector.csv',
                       help='Output file name')
    parser.add_argument('--model', type=str, default='gpt-5-nano',
                       help='OpenAI model to use (default: gpt-5-nano)')
    parser.add_argument('--temperature', type=float, default=1.0,
                       help='Model temperature (default: 1.0)')
    parser.add_argument('--max-input-length', type=int, default=2000,
                       help='Maximum input text length (default: 2000)')
    parser.add_argument('--batch-size', type=int, default=8,
                       help='Batch size (default: 8)')
    return parser.parse_args(argv)


#%%
if __name__ == "__main__":
    args = parse_args(['--test-mode', '--sample-size', '100'])
    print(args)
    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError("OPENAI_API_KEY is not set; please set it in .env file")
    TEST_MODE = args.test_mode
    data_dir = Path(args.data_dir)
    results_dir = Path(args.output_dir)
    prompt_path = args.prompt_file
    output_file_path = results_dir / args.output_file

    # load paragraphs from csv file
    df_paragraphs = pd.read_csv(results_dir / args.input_file)
    df_paragraphs = df_paragraphs[df_paragraphs['text'].notna()]
    df_paragraphs['id'] = df_paragraphs.index.astype(str)  # Ensure IDs are strings
    if TEST_MODE:
        df_paragraphs = df_paragraphs.sample(n=args.sample_size, random_state=42)

    # load prompt template and build batched messages
    prompt_messages_template = load_prompt(prompt_path).sections

    batch_messages, batch_ids = _build_batch_messages_from_df(
        df_paragraphs,
        prompt_messages_template,
        text_column='text',
        id_column='id',
        max_input_text_length=args.max_input_length,
    )

    # initiate batch agent for async inference
    model_args = {
        "api_key": os.getenv('OPENAI_API_KEY'),
        "model": args.model,
        "temperature": args.temperature,
    }
    batch_agent = BatchAsyncLLMAgent(**model_args)
    # run a test connection to ensure the agent is set up correctly
    asyncio.run(batch_agent.test_connection())
    # run a test with topic identification prompt
    response = asyncio.run(batch_agent.get_response_content(
        batch_messages[0],
        reasoning_effort='low',
        response_format=TopicResponse,
        max_completion_tokens=2000,
    ))
    print('reasoning:', response.reasoning)
    for topic in response.topic_labels:
        print(f"{topic.topic}: {topic.confidence}")

    # async batch run
    responses = asyncio.run(_process_batch_async(
        batch_agent,
        batch_messages,
        response_model=TopicResponse,
        batch_size=args.batch_size,
        max_completion_tokens=4000,
        safe_mode=True,
    ))

    # merge id with batch responses
    merged_results = _merge_ids_with_responses(batch_ids, responses)
    print(f"Processed {len(merged_results)} records")

    # convert response to wide format
    df_wide = _convert_response_to_wide_df(merged_results)
    print(df_wide.head())

    # merge back with original paragraphs on 'id'
    merged_df = df_paragraphs.merge(df_wide, on='id', how='left')
    # create dummy columns for topics where confidence > 30
    topic_columns = [col for col in df_wide.columns if col != 'id']
    for col in topic_columns:
        merged_df[f"{col}_dummy"] = (merged_df[col] > 30).astype(int)

    ## output to csv
    merged_df.to_csv(output_file_path, index=False)
    print(f"Output saved to {output_file_path}")


# %%




