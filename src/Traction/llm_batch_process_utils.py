#%%
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Callable, Type
import nest_asyncio
from pydantic import BaseModel

# Compute repository root from this file's location
# File is: <repo_root>/src/Traction/llm_batch_process_utils.py
# repo_root is 2 parents up
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / 'libs'))

import warnings
warnings.filterwarnings("ignore")
nest_asyncio.apply()
import pandas as pd  # keep original usage
from prompt_utils import load_prompt, format_messages
from llm_factory_openai import BatchAsyncLLMAgent  


#%%
def _safe_placeholder_format(template: str, format_data: Dict[str, str]) -> str:
    """Safely replace `{PLACEHOLDER}` tokens without interpreting other braces.

    We avoid `str.format(**format_data)` because many prompts contain JSON examples
    like `{"key": "value"}` which would otherwise be treated as format fields.
    """
    out = template
    for key, value in format_data.items():
        out = out.replace("{" + key + "}", value)
    return out


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


def _build_batch_messages_from_df_flexible(
    df: pd.DataFrame,
    prompt_template: Dict[str, str],
    *,
    column_mapping: Dict[str, str],
    id_column: str | None = None,
    max_text_length: int = 8000,
) -> Tuple[List[List[Dict[str, str]]], List[str]]:
    """Convert a dataframe into LLM-ready message batches with flexible column mapping.
    
    This function supports multiple columns mapped to template placeholders, enabling
    complex prompts that require multiple text fields (e.g., staff vs authority views).

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe containing the columns to be mapped.
    prompt_template : dict
        Template dict with keys like 'system', 'user'. The 'user' and/or 'system' 
        sections can contain placeholders (e.g., {STAFF}, {AUTHORITY}, {COUNTRY}).
    column_mapping : dict[str, str]
        Maps template placeholder names (UPPERCASE) to dataframe column names.
        Example: {'STAFF': 'staff_text', 'AUTHORITY': 'authority_text', 'COUNTRY': 'country'}
        All keys should be uppercase to match template placeholders.
    id_column : str | None
        Column to use as identifier. If None, dataframe index is used.
    max_text_length : int
        Truncate text fields to this many characters. Applied to all text-like columns.

    Returns
    -------
    batch_messages : list[list[dict]]
        List of message arrays ready for LLM processing.
    batch_ids : list[str]
        Corresponding identifiers for each message.

    Examples
    --------
    >>> column_mapping = {
    ...     'STAFF': 'staff_text',
    ...     'AUTHORITY': 'authority_text', 
    ...     'COUNTRY': 'country',
    ...     'YEAR': 'year'
    ... }
    >>> messages, ids = build_batch_messages_from_df_flexible(
    ...     df, prompt_template, column_mapping=column_mapping, id_column='index'
    ... )
    """
    # Validate that all mapped columns exist in dataframe
    missing_cols = [col for col in column_mapping.values() if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Columns {missing_cols} not found in dataframe. Available: {list(df.columns)}")
    
    if id_column is not None and id_column not in df.columns:
        raise ValueError(f"ID column '{id_column}' not found in dataframe. Available: {list(df.columns)}")

    batch_messages: List[List[Dict[str, str]]] = []
    batch_ids: List[str] = []

    # Iterate rows
    for idx, row in df.iterrows():
        row_id = row[id_column] if id_column else idx
        
        # Build mapping dict: PLACEHOLDER -> actual value from row
        format_data = {}
        for placeholder, col_name in column_mapping.items():
            raw_value = row[col_name]
            value = str(raw_value) if raw_value is not None else ""
            # Truncate text-like fields (strings that are not just numbers/years)
            if isinstance(raw_value, str):  # heuristic: long strings are text
                value = value.strip()[:max_text_length]
            format_data[placeholder] = value
        
        # Clone template and format both system and user sections
        this_template = prompt_template.copy()
        
        # Format system prompt if it exists and has placeholders
        if "system" in this_template:
            this_template["system"] = _safe_placeholder_format(this_template["system"], format_data)
        
        # Format user prompt (required)
        if "user" not in this_template:
            raise KeyError("Prompt template must contain a 'user' field.")
        this_template["user"] = _safe_placeholder_format(this_template["user"], format_data)
        
        messages = format_messages(this_template, add_schema=True)
        batch_messages.append(messages)
        batch_ids.append(str(row_id))

    return batch_messages, batch_ids

async def _process_batch_async(
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

