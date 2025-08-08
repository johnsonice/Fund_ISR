#%%
import pandas as pd
import os
import sys
import re  # Added for text processing functions
sys.path.insert(0, '../libs')
import copy
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
from llm_utils import BSAgent
from prompts import topic_identify_simple_pt
from dotenv import load_dotenv
# Load environment variables from project root .env file
env_path = '../.env'
load_dotenv(dotenv_path=env_path)

#%%
class TopicLabel(BaseModel):
    topic_label: str
    confidence_score: float

class TopicClassification(BaseModel):
    reasoning: str
    topic_labels: List[TopicLabel]

def check_result_errors(result_df: pd.DataFrame, filename: str = None) -> tuple[list, pd.DataFrame]:
    """Check for errors and null values in result dataframe and return error rows.
    
    Args:
        result_df: DataFrame containing results to check
        filename: Optional name of file being checked
        
    Returns:
        Tuple containing:
        - List of error messages
        - DataFrame containing only the error rows with filename column added
    """
    issues = []
    
    # Check for empty lists in topic labels
    error_mask = result_df['topic_labels'].apply(lambda x: x == '[]' or len(x) == 0 or x is None)
    empty_topic_labels = error_mask.sum()
    
    if empty_topic_labels > 0:
        pct_empty_topics = (empty_topic_labels / len(result_df)) * 100
        file_info = f" in {filename}" if filename else ""
        issues.append(f"Found {empty_topic_labels} ({pct_empty_topics:.1f}%) empty topic label lists{file_info}")
    
    # Extract error rows and add filename
    error_df = result_df[error_mask].copy()
    error_df['filename'] = filename
    
    return issues, error_df

def patch_error_rows(result_df: pd.DataFrame, agent: BSAgent) -> pd.DataFrame:
    """Patch rows with empty topic labels using synchronous agent."""
    # Find rows with empty topic labels
    error_mask = result_df['topic_labels'].apply(lambda x: x == '[]')
    error_rows = result_df[error_mask]
    
    if len(error_rows) == 0:
        return result_df
    
    print(f"Found {len(error_rows)} rows with errors to patch")
    
    # Process each error row
    for idx in error_rows.index:
        prompt = copy.deepcopy(topic_identify_simple_pt)
        prompt['user'] = prompt['user'].format(PARA=result_df.loc[idx, 'par'])
        
        try:
            response = agent.get_response_content(
                prompt_template=prompt,
                response_format=TopicClassification
            )
            # Update the row with new results
            result_df.loc[idx, 'topic_labels'] = [label.topic_label for label in response.topic_labels]
            result_df.loc[idx, 'confidence_scores'] = [label.confidence_score for label in response.topic_labels]
            result_df.loc[idx, 'reasoning'] = response.reasoning
            
        except Exception as e:
            print(f"Error processing row {idx}: {str(e)}")
            continue
    
    return result_df



def verify_results(input_dir: Path, 
                   output_dir: Path, 
                   patch_errors: bool = False,
                   agent: Optional[BSAgent] = None,
                   ignore_file_missing: bool = False
                   ):
    """Quick verification of result files against input files."""
    input_files = [f for f in input_dir.glob('*.csv') if not f.name.startswith('results_')]
    #print(input_files)
    issues = []
    files_with_errors = []
    total_error_count = 0
    all_error_rows = pd.DataFrame()
    
    # Step 1: Check for missing result files
    print("\nChecking for missing result files...")
    for input_file in input_files:
        result_file = output_dir / f"results_{input_file.name}"
        if not result_file.exists():
            issues.append(f"Missing: {input_file.name}")
    if issues:
        print("\nMissing result files:")
        for issue in issues:
            print(f"- {issue}")
        if not ignore_file_missing:
            return False, pd.DataFrame()
    
    # Step 3: Check for errors and collect statistics
    print("\nChecking for errors and collecting statistics...")
    result_files = [f for f in output_dir.glob('*.csv') if not f.name.startswith('.')]
    for result_file in result_files:
        result_file_path = output_dir / result_file.name
        result_df = pd.read_csv(result_file_path)
        
        error_issues, error_df = check_result_errors(result_df, result_file.name)
        if error_issues:
            files_with_errors.append(result_file.name)
            total_error_count += int(re.search(r'Found (\d+)', error_issues[0]).group(1))
            issues.extend(error_issues)
            all_error_rows = pd.concat([all_error_rows, error_df], ignore_index=True)
    
    if files_with_errors:
        print(f"\nError Statistics:")
        print(f"- Total files with errors: {len(files_with_errors)}")
        print(f"- Total error rows: {total_error_count}")
        print(f"- Average errors per file: {total_error_count/len(files_with_errors):.1f}")
    
    # Step 4: Patch errors if requested
    if patch_errors and files_with_errors:
        print("\nPatching errors...")
        for result_file in result_files:
            if result_file.name in files_with_errors:
                result_file_path = output_dir / result_file.name
                result_df = pd.read_csv(result_file_path)
                
                print(f"\nPatching errors in {result_file.name}")
                result_df = patch_error_rows(result_df, agent)
                result_df.to_csv(result_file_path, index=False)
                print(f"Saved patched results to {result_file}")
    
    # if issues:
    #     print("\nAll issues found: {}".format(len(issues)))
    # else:
    #     print("\nAll files verified successfully!")
    
    return len(issues) == 0, all_error_rows

#%%
if __name__ == "__main__":
    data_dir = Path('/ephemeral/home/xiong/data/Fund/CSR')

    agent = BSAgent(
        model='llama-3.1-8b-Instruct',
        api_key='abc',
        base_url='http://localhost:8000/v1'
    )
    # Test agent chat
    test_prompt = {"user": "Say hello!", "assistant": "I should respond with a greeting."}
    test_response = agent.get_response_content(prompt_template=test_prompt)
    print("Agent test response:", test_response)
    #%%
    # Verify all results
    error_flag, error_df = verify_results(
        data_dir / 'All_AIV_2008-2024_CSV',
        data_dir / 'All_AIV_2008-2024_CSV_topic_identify',
        patch_errors=False,
        agent=agent,
        ignore_file_missing=True
    ) 
    print("Error flag:", error_flag)
    print("\n # of issues found: {}".format(len(error_df)))
    error_report_path = data_dir /'error_report.csv'
    error_df.to_csv(error_report_path, index=False)
    print("Error file exported to :", error_report_path)
#%%
        

    # #%%
    # # Load example file
    # res_files = os.listdir(data_dir / 'All_AIV_2008-2024_CSV_topic_identify')
    # #%%
    # for i in range(len(res_files)):
    #     res_file = res_files[i]
    #     df = pd.read_csv(data_dir / 'All_AIV_2008-2024_CSV_topic_identify' / res_file)
    #     res = check_result_errors(df)
    #     if len(res) > 0:
    #         print(res_file, len(res))
    # #%%
    # # Initialize agent with environment variables
    # # agent = BSAgent(
    # #     model='gpt-4',
    # #     api_key=os.getenv("OPENAI_API_KEY")
    # # )
    #     # Patch errors in the example file
    # result_df = patch_error_rows(df, agent)