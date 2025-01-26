## batch inference with vllm
## before run this script, you need to start the vllm server
## CUDA_VISIBLE_DEVICES=6,7 python -m vllm.entrypoints.openai.api_server --model /home/xiong/data/hf_cache/llama-3.1-8B-Instruct --dtype auto --served-model-name llama-3.1-8b-Instruct --tensor-parallel-size 2 --api-key abc
#%%
import os
import sys
import re  # Added for text processing functions
sys.path.insert(0, '../libs')
import asyncio
import nest_asyncio
nest_asyncio.apply() 
import pandas as pd
from typing import Literal, List  # Consolidated typing imports
from pydantic import BaseModel
import copy
from pathlib import Path
from tqdm.asyncio import tqdm_asyncio
import tqdm
from llm_utils_async import AsyncBSAgent
from prompts import topic_identify_simple_pt
import nltk 

#%%

def flatten(nested_list):
    """
    Flattens a nested list.
    """
    flat_list = []
    for element in nested_list:
        if isinstance(element, list):
            flat_list.extend(flatten(element))
        else:
            flat_list.append(element)
    return flat_list

def _extract_tag(s):
    if isinstance(s,str):
        pattern = r'<(.*?)>' # Regular expression pattern to match the content inside the first pair of angle brackets
        match = re.search(pattern, s) # Search for the pattern in the string
        if match:   # If a match is found, return the content inside the brackets
            return match.group(1)
        else:
            return None
    else:
        return None

def _filter_by_tag(s,keep_tags=['title','para']):
    tag = _extract_tag(s)
    if tag:
        if tag.lower() in keep_tags:
            return True
    return False

def clean_text(text):
    return re.sub(r'^<.*?>\s*', '', text)

def process_df(input_df):
    '''
    Do some simple filtering by keep only para tag and long paragraphs 
    '''
    input_df['tag_filter']=input_df['par'].apply(_filter_by_tag,args=(['para'],))  
    input_df['length_filter'] = input_df['par'].apply(lambda s: len(s.split())>15)
    input_df = input_df[(input_df['tag_filter']) & (input_df['length_filter'])]
    input_df = input_df.drop(columns=['tag_filter','length_filter'])
    input_df['par'] = input_df['par'].apply(clean_text)

    return input_df

def accumulate_csv_files(directory,end_with='.csv',process_func=None):
    """
    This function reads all CSV files from a given directory and appends them into one DataFrame.
    """
    # List to hold dataframes
    dataframes = []
    # Iterate over all files in the directory
    for filename in os.listdir(directory):
        if filename.endswith(end_with):
            filepath = os.path.join(directory, filename)
            # Read the CSV file and append to the list
            df = pd.read_csv(filepath)
            if process_func:
                df = process_func(df)
            dataframes.append(df)
    # Concatenate all dataframes in the list
    combined_df = pd.concat(dataframes, ignore_index=True)
    
    return combined_df


class TopicLabel(BaseModel):
    topic_label: str
    confidence_score: float

class TopicClassification(BaseModel):
    reasoning: str
    topic_labels: List[TopicLabel]
    
def unit_test():
    agent = AsyncBSAgent(
        model='llama-3.1-8b-Instruct',
        base_url='http://localhost:8000/v1',
        api_key='abc'
    )
    # Simple test prompt template
    test_prompt = {
        "system": "You are a helpful assistant.",
        "user": "Say hello world"
    }

    # Run test inference
    response = asyncio.run(agent.get_response_content(prompt_template=test_prompt))
    print("Test Response:", response)
#%%
async def process_file(agent, 
                      input_file: Path, 
                      output_file: Path, 
                      prompt_template, 
                      batch_size=100):
    """Process a single CSV file in batches and save results"""
    print(f"Processing {input_file}")
    
    # Read input data and process it
    dataset = pd.read_csv(input_file)
    print('original length:', len(dataset))
    dataset = process_df(dataset)  # Apply the processing function
    dataset = dataset.reset_index(drop=True)  # Reset index after filtering
    total_rows = len(dataset)
    print('after processing: ', total_rows)
    all_results = []
    
    async def process_row(i):
        structured_prompt = copy.deepcopy(prompt_template)
        structured_prompt['user'] = structured_prompt['user'].format(
            PARA=dataset.iloc[i].par
        )
        try:
            # Add small delay before each request
            await asyncio.sleep(0.1)  # 100ms delay between individual requests
            response = await agent.get_response_content(
                prompt_template=structured_prompt, 
                response_format=TopicClassification
            )
            return {
                'index': i,  # Store the index to maintain alignment
                'paragraph': dataset.iloc[i].par,
                'topic_labels': [label.topic_label for label in response.topic_labels],
                'confidence_scores': [label.confidence_score for label in response.topic_labels],
                'reasoning': response.reasoning
            }
        except Exception as e:
            print(f"Error processing row {i} in {input_file.name}: {str(e)}")
            return {
                'index': i,  # Store the index to maintain alignment
                'paragraph': dataset.iloc[i].par,
                'topic_labels': [],
                'confidence_scores': [],
                'reasoning': f"Error: {str(e)}"
            }

    # Process in batches with progress bar
    with tqdm.tqdm(total=total_rows, desc=f"Processing {input_file.name}") as pbar:
        for batch_start in range(0, total_rows, batch_size):
            batch_end = min(batch_start + batch_size, total_rows)
            
            # Process current batch
            batch_tasks = [process_row(i) for i in range(batch_start, batch_end)]
            batch_results = await asyncio.gather(*batch_tasks)
            
            # Update progress and collect results
            all_results.extend(batch_results)
            pbar.update(len(batch_results))
            
            # Add delay between batches
            await asyncio.sleep(0.5)  # 2 second delay between batches
    
    # Convert results to DataFrame and ensure proper alignment
    results_df = pd.DataFrame(all_results)
    assert len(results_df) == len(dataset), "Results length doesn't match dataset length"
    assert (results_df['paragraph'] == dataset['par']).all(), "Paragraph alignment mismatch"
    dataset = dataset.reset_index(drop=True)  # Ensure clean index before merging
    dataset['original_text'] = results_df['paragraph']
    dataset['topic_labels'] = results_df['topic_labels']
    dataset['confidence_scores'] = results_df['confidence_scores']
    dataset['reasoning'] = results_df['reasoning']
    dataset.to_csv(output_file, index=False)

async def process_all_files(agent, input_files, output_dir, prompt_template):
    """Process all files using a single event loop"""
    for input_file in tqdm.tqdm(input_files, desc="Processing files"):
        output_file = output_dir / f"results_{input_file.name}"
        await process_file(
            agent, 
            input_file, 
            output_file, 
            prompt_template,
            batch_size=64
        )
#%%

if __name__ == "__main__":

    test_run = False
    
    agent = AsyncBSAgent(
        model='llama-3.1-8b-Instruct',
        base_url='http://localhost:8000/v1',
        api_key='abc'
    )
    # Define input and output directories
    data_dir = Path('/ephemeral/home/xiong/data/Fund/CSR')
    input_dir = data_dir / 'All_AIV_2008-2024_CSV'
    output_dir = data_dir / 'All_AIV_2008-2024_CSV_topic_identify'
    output_dir.mkdir(exist_ok=True)
    
    # Get all CSV files to process
    if test_run:
        input_files = list(input_dir.glob('*.csv'))[:2]
    else:
        input_files = list(input_dir.glob('*.csv'))
    # Filter out files that start with 'results_' or already exist in output_dir
    input_files = [f for f in input_files 
                  if not f.name.startswith('results_') and 
                  not (output_dir / f"results_{f.name}").exists()]
    print(f"Found {len(input_files)} files to process")
    
    # Run everything in a single event loop
    asyncio.run(process_all_files(
        agent,
        input_files,
        output_dir,
        topic_identify_simple_pt
    ))

# %%
