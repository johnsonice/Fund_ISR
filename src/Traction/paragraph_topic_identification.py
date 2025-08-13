#%%
import json,os,sys,time,glob
from pathlib import Path
from typing import List, Dict, Any, Tuple, Callable, Type
import asyncio,nest_asyncio
from tqdm import tqdm
from pydantic import BaseModel

sys.path.insert(0, str('../../'))
import warnings
warnings.filterwarnings("ignore")
nest_asyncio.apply()
import pandas as pd  # keep original usage
from libs.prompt_utils import load_prompt, format_messages
from libs.llm_factory_openai import BatchAsyncLLMAgent  
from libs.prompt_utils import load_prompt, format_messages 
import config
from dotenv import load_dotenv
load_dotenv('../../.env') ## load api key from .env file

#%%
def _build_batch_messages_from_df(
    df: pd.DataFrame,
    prompt_template: Dict[str, str],
    *,
    text_column: str = "text",
    id_column: str | None = None,
    max_input_text_length: int = 2000,
) -> Tuple[List[List[Dict[str, str]]], List[str]]:
    """Convert a dataframe of paragraphs into LLM-ready message batches.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe containing text and (optionally) an ID column.
    prompt_template : dict
        Template with a 'user' key containing a {TEXT} placeholder.
    text_column : str
        Column name holding the text to classify.
    id_column : str | None
        Column to use as identifier. If None, dataframe index is used.
    max_input_text_length : int
        Truncate text to this many characters.
    """
    if text_column not in df.columns:
        raise ValueError(f"Column '{text_column}' not found in dataframe. Available: {list(df.columns)}")
    if id_column is not None and id_column not in df.columns:
        raise ValueError(f"ID column '{id_column}' not found in dataframe. Available: {list(df.columns)}")

    batch_messages: List[List[Dict[str, str]]] = []
    batch_ids: List[str] = []

    # Iterate rows; use provided id column or index
    for idx, row in df.iterrows():
        raw_text = row[text_column]
        text = str(raw_text) if raw_text is not None else ""
        text = text.strip()[:max_input_text_length]
        row_id = row[id_column] if id_column else idx

        # Clone and inject
        this_template = prompt_template.copy()
        if "user" not in this_template:
            raise KeyError("Prompt template must contain a 'user' field with a {TEXT} placeholder.")
        this_template["user"] = this_template["user"].format(TEXT=text)
        messages = format_messages(this_template, add_schema=True)

        batch_messages.append(messages)
        batch_ids.append(str(row_id))

    return batch_messages, batch_ids

async def _process_articles_async(
    agent: BatchAsyncLLMAgent,
    batch_messages: List[List[Dict[str, str]]],
    response_model: Type[BaseModel],
    batch_size: int = 16,
    max_completion_tokens: int = 4000,
    results_post_process: Callable[[List[Any]], List[Any]] = lambda x: x,
    **kwargs,
) -> List[Any]:
    """Run batched inference and post-process the results."""

    contents = await agent.get_batch_response_contents_auto(
        batch_messages,
        batch_size=batch_size,  # how many chat threads are sent per HTTP request
        max_completion_tokens=max_completion_tokens,  # generation budget per completion
        response_format=response_model,  # Pydantic model enforcing JSON schema
        **kwargs,
    )
    return results_post_process(contents)


def _merge_ids_with_responses(ids: List[str], responses: List[Any]) -> List[Dict[str, Any]]:
    """Attach article IDs to response models or error strings."""

    merged: List[Dict[str, Any]] = []
    for msg_id, content in zip(ids, responses):
        if isinstance(content, BaseModel):
            # Successful response: turn the pydantic model into a raw dict.
            record: Dict[str, Any] = content.dict()
        else:
            # Failure mode (e.g., malformed JSON).  Preserve the error string
            # so downstream analysts can inspect / retry these cases.
            record = {
                "error": str(content),
            }
        record["id"] = msg_id
        merged.append(record)
    return merged


#%%

if __name__ == "__main__":
    from prompts.schema import TopicResponse
    
    TEST_MODE = True
    # data_dir = config.data_dir
    data_dir = Path('/data/home/xiong/data/Fund/CSR/Tractions/')
    results_dir = data_dir / 'output'
    prompt_path = "./prompts/topic_classification.md"
    
    ## load paragraphs from csv file
    df_paragraphs = pd.read_csv(results_dir / 'df_paragraphs.csv')
    df_paragraphs = df_paragraphs[df_paragraphs['text'].notna()]
    df_paragraphs['id'] = df_paragraphs.index.astype(str)  # Ensure IDs are strings
    if TEST_MODE:
        df_paragraphs = df_paragraphs.sample(n=100, random_state=42)

    ## load prompt template and build batched messages
    prompt_messages_template = load_prompt(prompt_path).sections
    batch_messages, batch_ids = _build_batch_messages_from_df(
        df_paragraphs,
        prompt_messages_template,
        text_column='text',
        id_column='id',  # Now used inside function
        max_input_text_length=2000
    )

    ## initiate batch agent for async inference
    model_args = {
        "api_key": os.getenv('OPENAI_API_KEY'),
        "model": 'gpt-5-nano',
        "temperature": 1
    }
    batch_agent = BatchAsyncLLMAgent(**model_args)
    
    ## run a test connection to ensure the agent is set up correctly
    asyncio.run(batch_agent.test_connection())
    response = await batch_agent.get_response_content(batch_messages[0],
                                                      reasoning_effort='low',
                                                      response_format=TopicResponse,
                                                      max_completion_tokens=2000)
    print('reasoning:',response.reasoning)
    for topic in response.topic_labels:
        print(f"{topic.topic}: {topic.confidence}")
        
    ## async batch run 
    responses = asyncio.run(
            _process_articles_async(
                batch_agent,
                batch_messages,
                response_model=TopicResponse,
                batch_size=8,
                max_completion_tokens=4000,
                safe_mode=True,
            )
        )
    ## merge id with batch responses 
    merged_results = _merge_ids_with_responses(batch_ids, responses)