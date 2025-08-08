#%%
# load libraries
import os,sys
sys.path.insert(0,'../src')
sys.path.insert(0,'../libs')
import pandas as pd
import numpy as np
from pathlib import Path
from prompts import topic_identify_simple_pt
from llm_utils import BSAgent
from dotenv import load_dotenv
# Load environment variables from project root .env file
env_path = '../.env'
load_dotenv(dotenv_path=env_path)

#%%
def load_all_results(result_dir: Path, filter_empty_topics: bool = True) -> pd.DataFrame:
    """Load and concatenate all CSV files from the result directory.
    Args:
        result_dir: Path to directory containing result CSV files
        filter_empty_topics: If True, filter out rows where topic_labels is '[]'
        
    Returns:
        Combined DataFrame containing all results
    """
    # Get list of all CSV files (excluding hidden files)
    result_files = [f for f in result_dir.glob('*.csv') if not f.name.startswith('.')]
    # Load and concatenate all files
    all_results = []
    for result_file in result_files:
        df = pd.read_csv(result_file)
        df['source_file'] = result_file.name  # Add source filename as column
        all_results.append(df)
    
    # Combine all dataframes
    combined_df = pd.concat(all_results, ignore_index=True)
    
    # Filter out empty topic labels if requested
    if filter_empty_topics:
        combined_df = combined_df[combined_df['topic_labels'] != '[]']
    
    return combined_df

def get_topic_frequencies(df: pd.DataFrame,column_name: str) -> dict:
    """Get frequencies of all unique topic labels in the dataframe.
    
    Args:
        df: DataFrame containing 'topic_labels' column with lists of topics
        
    Returns:
        Dictionary mapping topic labels to their frequencies
    """
    # Get all unique topics and their frequencies by flattening the lists
    topic_frequencies = {}
    for topics in df[column_name]:
        if isinstance(topics, list):
            for topic in topics:
                topic_frequencies[topic] = topic_frequencies.get(topic, 0) + 1
        else:
            topic_frequencies[topics] = topic_frequencies.get(topics, 0) + 1
            
    return dict(sorted(topic_frequencies.items(), key=lambda x: x[1], reverse=True))

def llm_keytopic_harmonization(topic_freqs: dict):
    key_phrases = '||'.join(topic_freqs.keys())
    topic_definitions = topic_identify_simple_pt['user'].split('----------------')[2]
    sys_message = '''
    You are an experienced IMF economist. You are given:
    1. A list of unique key phrases separated by “||”.
    2. A set of topic definitions.

    Your task is to:
    - Assign each key phrase to the most appropriate topic based on the provided definitions.  
    - Return the result as a dictionary (e.g., JSON) where each key is the exact key phrase (case-sensitive), and each value is the corresponding topic label (without any `**` characters).

    Your output should include only this dictionary, with no additional commentary.
    '''
    user_message = '''
    Here are the key phrases:
    ```
    {TOPIC_KEY_PHRASES}
    ```

    Here are the topic definitions:
    ```
    {TOPIC_DEFINITIONS}
    ```

    **Task:** Assign each key phrase to its most appropriate topic from the definitions.
    **Format:** Return your answer in **clean JSON** with each key phrase (case-sensitive) as the key and the corresponding topic as the value. For example:

    ```json
    {{
    "key1": "topic1",
    "key2": "topic2"
    }}
    ```
    No additional commentary or formatting is required.
    '''.format(TOPIC_KEY_PHRASES=key_phrases, TOPIC_DEFINITIONS=topic_definitions)
        

    agent = BSAgent(
        model='gpt-4o',
        api_key=os.getenv('OPENAI_API_KEY'),
        temperature=0.1
    )
    res = agent.get_response_content(prompt_template={
                                'system': sys_message,
                                'user': user_message
                            })
    
    topic_map = agent.parse_load_json_str(res)
    # Verify all keys in topic_freqs exist in topic_map
    missing_keys = set(topic_freqs.keys()) - set(topic_map.keys())
    if missing_keys:
        print(f"Missing topic mappings for: {missing_keys}")
        
    return topic_map, missing_keys
#%%
if __name__ == '__main__':
    # load data
    manual_update = True
    load_existing_results = True
    data_dir = Path('/ephemeral/home/xiong/data/Fund/CSR')
    result_dir = data_dir / 'All_AIV_2008-2024_CSV_topic_identify'
    process_data_stage1 = data_dir / 'All_AIV_2008-2024_CSV_topic_identify_consolidated.csv'
    metadata_path = data_dir / 'meta_data' / 'All_AIV_2008-2024_meta.xlsx'
    process_data_stage2 = data_dir / 'All_AIV_2008-2024_CSV_topic_identify_consolidated_with_metadata.csv'
    country_map_path = data_dir / 'meta_data' / 'country_map.xlsx'
    #%%
    if load_existing_results:
        all_results_df = pd.read_csv(process_data_stage1)
    else:
        all_results_df = load_all_results(result_dir)
        print(f"Loaded {len(all_results_df):,} total rows from {all_results_df['source_file'].nunique()} files")
        # Convert string representation of lists to actual lists
        all_results_df['topic_labels'] = all_results_df['topic_labels'].apply(eval)
        topic_freqs = get_topic_frequencies(all_results_df,'topic_labels')
        topic_map, missing_keys = llm_keytopic_harmonization(topic_freqs)
        #### inspect missing keys an manually update topic map
        ### manual update map harmonize topic labels
        if manual_update:
            input_missing_keys = input(f"you should stop here and update the topic map for the following missing keys: {missing_keys}")
            raise ValueError('Stop here')
            ### this is on example
            add_dict = {'Debt and Fiscal Sustainability': 'Fiscal Policy',
            'Regulatory Framework is not a predefined topic, but it is a subtopic of Structural Reforms, so I will not use it as a topic label. However, I will use the closest predefined topic which is Structural Reforms.': 'Structural Reforms',
            'Program risks': 'Other Topics'}
            topic_map.update(add_dict)
            ## check again after manual update 
            missing_keys = set(topic_freqs.keys()) - set(topic_map.keys())
            if missing_keys:
                print(f"Missing topic mappings for: {missing_keys}")
        
        # Extract first topic from topic_labels list and map to consolidated topics
        all_results_df['consolidated_topic_labels'] = all_results_df['topic_labels'].apply(lambda x: topic_map.get(x[0]) if isinstance(x, list) and len(x) > 0 else None)
        print(all_results_df.head())
        topic_freqs = get_topic_frequencies(all_results_df,'consolidated_topic_labels')
        print(topic_freqs)
        # save the results
        all_results_df.to_csv(process_data_stage1,index=False)
    
    #%%
    ##############
    #### merge basic document metadata
    #############
    # add metadata to the results
    metadata_df = pd.read_excel(metadata_path)

    all_results_df = pd.merge(all_results_df, metadata_df, left_on='File_Name', right_on='File Name', how='left')
    all_results_df = all_results_df.drop('File Name', axis=1)  # Remove redundant column
    print(f"Merged data shape: {all_results_df.shape}")

    # Check for unmatched observations
    unmatched = all_results_df[all_results_df['Country_Name'].isna()]
    if len(unmatched) > 0:
        print(f"\nFound {len(unmatched)} unmatched rows:")
        print(f"Unmatched File_Names:\n{unmatched['File_Name'].unique().tolist()}")
    ## Drop for the time being 
    input_drop = input(f"you should stop here and decide if you want to drop rows for the time being:")
    if input_drop.lower() == 'y':
        all_results_df = all_results_df.dropna(subset=['Country_Name'])
    #%%
    ##############
    #### merge country meta information
    #############
    keep_cols = ['ifscode','income','ISO-3 code','ISO-2 code']
    country_map_df = pd.read_excel(country_map_path)[keep_cols]
    all_results_df['Country Code'] = all_results_df['Country Code'].astype(int)
    all_results_df['Year'] = all_results_df['Year'].astype(int)
    #%%
    all_results_df = pd.merge(all_results_df, country_map_df, 
                                   left_on='Country Code', 
                                   right_on='ifscode', 
                                   how='left')
    all_results_df = all_results_df.drop('ifscode', axis=1)
    #%%
    #######
    # remove appendix and annex
    # Remove entries containing "appendix" or "annex" in section or sub_section (case-insensitive)
    #######
    original_len = len(all_results_df)
    all_results_df = all_results_df[~(
        all_results_df['section'].str.contains('appendix|annex', case=False, na=False) |  
        all_results_df['sub_section'].str.contains('appendix|annex', case=False, na=False)
    )]
    print(f"Removed {original_len - len(all_results_df)} rows containing 'Appendix' or 'Annex' in section/sub_section")

    #%%
    # Save merged results
    all_results_df.to_csv(process_data_stage2, index=False)

# %%
