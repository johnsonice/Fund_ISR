"""
Evaluation script for fine-tuned GPT-5-mini model.

Runs inference on test set and calculates comprehensive metrics for
monetary stance classification.
"""
#%%
#%%
# Setup
import os, sys
from pathlib import Path
from dotenv import load_dotenv
import json
from datetime import datetime
import training_config as config
PROJECT_ROOT = config.PROJECT_ROOT
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'libs'))
sys.path.insert(0, str(PROJECT_ROOT / 'src/Traction'))
sys.path.insert(0, str(PROJECT_ROOT / 'src/Traction/prompts'))
load_dotenv(PROJECT_ROOT / '.env')

from llm_factory_openai import LLMAgent
# Use _process_batch_async to process batch_messages
import asyncio
from llm_batch_process_utils import _process_batch_async
from llm_factory_openai import BatchAsyncLLMAgent
from llm_batch_process_utils import _merge_ids_with_responses

from prompt_utils import load_prompt, format_messages
from schema import PROMPT_REGISTRY
from pathlib import Path
import pandas as pd
from utils import load_jsonl, load_json
from typing import List, Dict, Any, Tuple
from sklearn.metrics import f1_score, accuracy_score, confusion_matrix, precision_score, recall_score

#%%
def load_parse_test_jsonl(test_file: Path) -> List[Dict[str, Any]]:
    """
    Load and parse test JSONL file.
    """
    data = load_jsonl(test_file)
    messages = []
    labels = []
    for msgs in data:
        messages.append(msgs['messages'][:2])
        labels.append((json.loads(msgs['messages'][2]['content'])))
    return messages, labels

def _convert_response_models_to_dicts(results: List[Any],
                                      structured_output: bool = False) -> List[Dict[str, Any]]:
    results_dicts = []
    if not structured_output:
        for result in results:
            if result is not None:
                result_dict = json.loads(result)
                results_dicts.append(result_dict)
            else:
                results_dicts.append(None)
    else:
        for result in results:
            if result is not None:
                result_dict = {
                    'stance_current': result.stance_current,
                    'stance_future': result.stance_future
                }
                results_dicts.append(result_dict)
            else:
                results_dicts.append(None)
    return results_dicts

def evaluate_monetary_stance(model_results: List[Dict[str, Any]], 
                             labels: List[str],
                             key: str,
                             combine_unclear_irrelevant: bool = False) -> Dict[str, Any]:
    """
    Evaluate monetary stance classification model.
    """
    ## process model_results dict and labels dict on a specific key and calculate ecaluation metrics
    temp_labels = [label[key] for label in labels]
    temp_model_results = [result[key] for result in model_results]
    if combine_unclear_irrelevant:
        temp_labels = [label if label != 'unclear' and label != 'irrelevant' else 'unclear' for label in temp_labels]
        temp_model_results = [result if result != 'unclear' and result != 'irrelevant' else 'unclear' for result in temp_model_results]
    accuracy = accuracy_score(temp_labels, temp_model_results)
    precision = precision_score(temp_labels, temp_model_results, average='weighted', zero_division=0)
    recall = recall_score(temp_labels, temp_model_results, average='weighted', zero_division=0)
    f1 = f1_score(temp_labels, temp_model_results, average='weighted', zero_division=0)
    return accuracy, precision, recall, f1

#%%
def eval_trained_model(model_name: str,structured_output: bool = False):
    """
    Main function.
    """
    temperature = config.TEMPERATURE
    batch_size = 8
    max_completion_tokens = 2000
    #reasoning_effort = 'low'
    if structured_output:
        response_model = PROMPT_REGISTRY['monetary_stance_simple']['response_model']
    else:
        response_model = None
    
    batch_messages, labels = load_parse_test_jsonl(config.TEST_JSONL)
    #batch_messages, labels = batch_messages[:8], labels[:8]
    print(f"\nProcessing with {model_name} (temperature={temperature}, batch_size={batch_size})...")
    
    sync_agent = LLMAgent(
        api_key=os.getenv('OPENAI_API_KEY'),
        model=model_name,
        temperature=temperature,
    )
    batch_agent = BatchAsyncLLMAgent(
        api_key=os.getenv('OPENAI_API_KEY'),
        model=model_name,
        temperature=temperature,
    )
    ## test single message
    sync_results = sync_agent.get_response_content(batch_messages[0], response_format=response_model, 
                                                   max_completion_tokens=max_completion_tokens)
    if structured_output:
        print('current stance: {}, future stance: {}'.format(sync_results.stance_current, sync_results.stance_future))
    else:
        sync_results = json.loads(sync_results)
        print('current stance: {}, future stance: {}'.format(sync_results['stance_current'], sync_results['stance_future']))
    
    ## run batch results 
    async def run_batch():
        results = await _process_batch_async(
            batch_agent,
            batch_messages,
            response_model=response_model,
            batch_size=batch_size,
            max_completion_tokens=max_completion_tokens,
        )
        return results
    
    async_results = asyncio.run(run_batch())
    results_dicts = _convert_response_models_to_dicts(async_results,structured_output)
    
    Output_results = {'non_combined': {}, 'combined': {}}
    ## evaluate current stance
    for key in ['stance_current', 'stance_future']:
        accuracy, precision, recall, f1 = evaluate_monetary_stance(results_dicts, labels, key)
        print(f"{key} accuracy: {accuracy}, precision: {precision}, recall: {recall}, f1: {f1}")
        Output_results['non_combined'][key] = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
    ## evaluate with combined 'unclear' and 'irrelevant' labels
    print('\nEvaluating with combined \'unclear\' and \'irrelevant\' labels...\n')
    for key in ['stance_current', 'stance_future']:
        accuracy, precision, recall, f1 = evaluate_monetary_stance(results_dicts, labels, key, combine_unclear_irrelevant=True)
        print(f"{key} (combined unclear/irrelevant) accuracy: {accuracy}, precision: {precision}, recall: {recall}, f1: {f1}")
        Output_results['combined'][key] = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
    return Output_results

def write_evaluation_report(structured_results, non_structured_results, model_name):
    """Write evaluation results to markdown file."""
    all_results = {
        'Structured Output': structured_results,
        'Non-Structured Output': non_structured_results
    }
    
    report_lines = [
        "# Fine-Tuned Model Evaluation Report",
        "",
        f"**Model**: `{model_name}`",
        f"**Evaluation Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ]
    
    for output_type, results in all_results.items():
        report_lines.extend([
            f"## {output_type}",
            "",
            "| Task | Standard Acc | Standard F1 | Combined Acc | Combined F1 |",
            "|------|--------------|-------------|--------------|-------------|"
        ])
        
        for task in ['stance_current', 'stance_future']:
            std_metrics = results['non_combined'][task]
            comb_metrics = results['combined'][task]
            report_lines.append(
                f"| {task} | {std_metrics['accuracy']:.4f} | {std_metrics['f1']:.4f} | "
                f"{comb_metrics['accuracy']:.4f} | {comb_metrics['f1']:.4f} |"
            )
        
        report_lines.append("")
    
    with open(config.EVALUATION_REPORT_MD, 'w') as f:
        f.write('\n'.join(report_lines))
    
    print(f"Evaluation report written to: {config.EVALUATION_REPORT_MD}")
#%%
if __name__ == "__main__":
    model_name = 'ft:gpt-4.1-mini-2025-04-14:protagolabs:monetary-stance:CTwfIXWf' #config.BASE_MODEL
    #model_name = 'ft:gpt-4.1-mini-2025-04-14:protagolabs:monetary-stance:CTwfH1lc:ckpt-step-462'
    #model_name = 'ft:gpt-4.1-mini-2025-04-14:protagolabs:monetary-stance:CTwfIEFw:ckpt-step-924'
    structured_results = eval_trained_model(model_name,structured_output=True)
    non_structured_results = eval_trained_model(model_name,structured_output=False)
    # Write results to file
    write_evaluation_report(structured_results, non_structured_results, model_name)
# %%
