# %% [markdown]
# ### Semi-Automated Evaluation Pipeline on variations of prompts and models

# %%
# Setup
from dotenv import load_dotenv
load_dotenv('../../.env')
import os, sys
sys.path.insert(0, '../../libs')
sys.path.insert(0, '../../src/Traction/prompts')
sys.path.insert(0, '../../src/Traction')

from llm_factory_openai import LLMAgent
# Use _process_batch_async to process batch_messages
import asyncio
from llm_batch_process_utils import _process_batch_async
from llm_factory_openai import BatchAsyncLLMAgent
from llm_batch_process_utils import _merge_ids_with_responses

from prompt_utils import load_prompt, format_messages
from schema import PROMPT_REGISTRY
from prompt_examples import (
    AUTHOR_TYPE_MAPPING,
    AUTHOR_TYPE_POSSESSIVE_MAPPING,
    AUTHOR_VERB_MAPPING,
    TASK_EXAMPLES,
    TASK_EXPLANATIONS,
    TASK_GROUND_TRUTH_COLS,
    TASK_COLUMN_MAPPINGS
)
from pathlib import Path
import pandas as pd
from llm_batch_process_utils import _build_batch_messages_from_df_flexible
from sklearn.metrics import f1_score, accuracy_score, confusion_matrix, precision_score, recall_score

# %% Configuration Constants
DATA_FILE_PATHS = {
    'fiscal_stance': Path('/data/home/xiong/data/Fund/CSR/Tractions/Finetuning_data/labelled_fiscal_v2.xlsx'),
    'fiscal_agreement': Path('/data/home/xiong/data/Fund/CSR/Tractions/Finetuning_data/labelled_fiscal_v2.xlsx'),
    'monetary_stance': Path('/data/home/xiong/data/Fund/CSR/Tractions/Finetuning_data/labelled_monetary_v6.xlsx'),
    'monetary_agreement': Path('/data/home/xiong/data/Fund/CSR/Tractions/Finetuning_data/labelled_monetary_v6.xlsx'),
}

PROMPT_DIR = Path('../../src/Traction/prompts')
AGREEMENT_LABELS = ['disagreement exists', 'mostly agree', 'irrelevant']
STANCE_FIELDS = {
    'fiscal_stance': ['stance_near_term'],
    'monetary_stance': ['stance_current', 'stance_future']
}

# %% Helper Functions
def _get_task_type(prompt_key: str) -> str:
    """Extract task type from prompt key."""
    for prefix in ['monetary_stance', 'monetary_agreement', 'fiscal_stance', 'fiscal_agreement']:
        if prompt_key.startswith(prefix):
            return prefix
    raise ValueError(f"Unknown prompt type for key: {prompt_key}")


def _calculate_agreement_metrics(y_true, y_pred) -> dict:
    """Calculate all agreement classification metrics."""
    return {
        'accuracy': accuracy_score(y_true, y_pred),
        'f1_weighted': f1_score(y_true, y_pred, average='weighted', zero_division=0),
        'f1_macro': f1_score(y_true, y_pred, average='macro', zero_division=0),
        'precision_weighted': precision_score(y_true, y_pred, average='weighted', zero_division=0),
        'recall_weighted': recall_score(y_true, y_pred, average='weighted', zero_division=0),
        'confusion_matrix': confusion_matrix(y_true, y_pred, labels=AGREEMENT_LABELS)
    }


def _calculate_stance_field_metrics(df_merged, field) -> dict:
    """Calculate metrics for a single stance field."""
    y_true = df_merged[field]
    y_pred = df_merged[f"{field}_llm"]

    mask = y_true.notna() & y_pred.notna()
    y_true_clean = y_true[mask]
    y_pred_clean = y_pred[mask]

    if len(y_true_clean) == 0:
        return {}

    metrics = {
        f'{field}_accuracy': accuracy_score(y_true_clean, y_pred_clean),
        f'{field}_f1_weighted': f1_score(y_true_clean, y_pred_clean, average='weighted', zero_division=0),
        f'{field}_f1_macro': f1_score(y_true_clean, y_pred_clean, average='macro', zero_division=0),
    }

    # Merged variant (unclear/irrelevant)
    y_true_m = y_true_clean.apply(lambda x: 'unclear' if x == 'irrelevant' else x)
    y_pred_m = y_pred_clean.apply(lambda x: 'unclear' if x == 'irrelevant' else x)
    metrics[f'{field}_accuracy_merge_unclear'] = accuracy_score(y_true_m, y_pred_m)
    metrics[f'{field}_f1_weighted_merge_unclear'] = f1_score(y_true_m, y_pred_m, average='weighted', zero_division=0)

    return metrics


def _calculate_stance_metrics(df_merged, task_type) -> dict:
    """Calculate all stance metrics."""
    stance_fields = STANCE_FIELDS.get(task_type, [])
    metrics = {}

    for field in stance_fields:
        if field in df_merged.columns and f"{field}_llm" in df_merged.columns:
            field_metrics = _calculate_stance_field_metrics(df_merged, field)
            metrics.update(field_metrics)

    # Calculate averages
    if metrics:
        avg_keys = [k for k in metrics.keys() if 'accuracy' in k]
        metrics['average_accuracy'] = sum(metrics[k] for k in avg_keys) / len(avg_keys) if avg_keys else 0

        f1w_keys = [k for k in metrics.keys() if 'f1_weighted' in k]
        metrics['average_f1_weighted'] = sum(metrics[k] for k in f1w_keys) / len(f1w_keys) if f1w_keys else 0

        f1m_keys = [k for k in metrics.keys() if 'f1_macro' in k]
        metrics['average_f1_macro'] = sum(metrics[k] for k in f1m_keys) / len(f1m_keys) if f1m_keys else 0

    return metrics


# %% Data Loading
def load_transform_data(data_file: Path, task_type: str):
    """
    Load + transform evaluation data for a given task type.

    Updated (v2): we now read from a single labelled Excel file rather than
    separate train/test files.
    """
    if task_type not in ['monetary_agreement', 'fiscal_agreement', 'fiscal_stance', 'monetary_stance']:
        raise ValueError(f"Unknown task type: {task_type}")

    df_raw = pd.read_excel(data_file)

    if 'agreement' in task_type:
        # Agreement task: staff + authority texts side-by-side
        df_agree = df_raw[['index', 'Print ISBN', 'staff', 'buff', 'country', 'year', 'agreement_general', 'disagreement_areas']].copy()
        ground_truth_cols = TASK_GROUND_TRUTH_COLS[task_type]
        column_mapping = TASK_COLUMN_MAPPINGS['agreement']
        return df_agree, column_mapping, ground_truth_cols

    # Stance task: reshape into long form with one text per row (staff/buff)
    df_stance = pd.DataFrame()
    for tp in ['staff', 'buff']:
        if task_type == 'fiscal_stance':
            stance_cols = [f'{tp}_stance_near_term']
        else:
            stance_cols = [f'{tp}_stance_current', f'{tp}_stance_future']

        cols = ['index', 'Print ISBN', 'country', 'year', tp] + stance_cols
        df_temp = df_raw[cols].copy()
        df_temp = df_temp.rename(columns={tp: 'text'}).rename(columns={c: c.replace(tp + '_', '') for c in df_temp.columns})
        df_temp['type'] = tp
        df_stance = pd.concat([df_stance, df_temp], ignore_index=True)

    # Get task-specific examples and explanations from imported constants
    example_dict = TASK_EXAMPLES.get(task_type, {})
    explanation_dict = TASK_EXPLANATIONS.get(task_type, {})
    ground_truth_cols = TASK_GROUND_TRUTH_COLS[task_type]

    df_stance['author_type'] = df_stance['type'].map(AUTHOR_TYPE_MAPPING)
    df_stance['type_possessive'] = df_stance['type'].map(AUTHOR_TYPE_POSSESSIVE_MAPPING)
    df_stance['verb'] = df_stance['type'].map(AUTHOR_VERB_MAPPING)
    df_stance['examples'] = df_stance['type'].map(example_dict).fillna('')
    df_stance['explanation'] = df_stance['type'].map(explanation_dict).fillna('')

    column_mapping = TASK_COLUMN_MAPPINGS['stance']

    return df_stance, column_mapping, ground_truth_cols


# %%
def evaluate_prompt_and_model(
    prompt_key: str,
    model_name: str = 'gpt-5',
    data_file: Path | None = None,
    temperature: float = 1.0,
    batch_size: int = 8,
    reasoning_effort: str = 'medium',
    max_completion_tokens: int = 2000,
    use_full_dataset: bool = True,
    return_dataframe: bool = False,
    verbose: bool = True,
):
    """
    High-level function to evaluate different prompt strategies and models.
    
    Parameters:
    -----------
    prompt_key : str
        Key from PROMPT_REGISTRY (e.g., 'monetary_agreement_simple', 'fiscal_stance_few_shot')
    model_name : str
        OpenAI model name (e.g., 'gpt-5', 'gpt-5-nano')
    temperature : float
        Temperature for LLM generation (default: 1.0)
    batch_size : int
        Number of messages to process in parallel (default: 8)
    reasoning_effort : str
        Reasoning effort level: 'minimal','low', 'medium', 'high' (default: 'medium')
    max_completion_tokens : int
        Maximum tokens for completion (default: 2000)
    use_full_dataset : bool
        Updated (v2): data comes from a single labelled file. If True, use the full file;
        if False, use a small random sample for quick iteration (default: True).
    return_dataframe : bool
        If True, return (metrics, dataframe); if False, return only metrics (default: False)
    
    Returns:
    --------
    dict or tuple
        Metrics dict with accuracy, f1_score, precision, recall, confusion_matrix
        If return_dataframe=True, returns (metrics, df_results)
    
    Example:
    --------
    # Test different prompts with the same model
    metrics = evaluate_prompt_and_model('monetary_agreement_simple', 'gpt-5')
    metrics = evaluate_prompt_and_model('monetary_agreement_few_shot', 'gpt-5')
    
    # Test same prompt with different models
    metrics = evaluate_prompt_and_model('fiscal_stance_simple', 'gpt-5')
    metrics = evaluate_prompt_and_model('fiscal_stance_simple', 'gpt-5-nano')
    """
    
    # Step 1: Get task type
    task_type = _get_task_type(prompt_key)
    # Auto-set temperature based on model type if not explicitly overridden
    # GPT-4o series: temperature = 0 (deterministic)
    # GPT-5 series: temperature = 1 (default reasoning)
    if temperature == 1.0:  # Only auto-set if user hasn't specified custom temperature
        if 'gpt-4o' in model_name.lower():
            temperature = 0.0
        # gpt-5 series already defaults to 1.0, no change needed

    # Step 2: Load data
    if data_file is None:
        data_file = DATA_FILE_PATHS.get(task_type)

    sample_df, column_mapping, ground_truth_cols = load_transform_data(data_file, task_type)

    if not use_full_dataset:
        sample_df = sample_df.sample(n=min(200, len(sample_df)), random_state=42)

    # Step 3: Load prompt
    registry_entry = PROMPT_REGISTRY[prompt_key]
    prompt_template = load_prompt(PROMPT_DIR / registry_entry["prompt_file"]).sections
    response_model = registry_entry["response_model"]
    
    # Step 4: Build messages
    batch_messages, batch_ids = _build_batch_messages_from_df_flexible(
        sample_df, prompt_template, column_mapping=column_mapping,
        id_column='index', max_text_length=8000
    )

    if verbose:
        print(f"Built {len(batch_messages)} messages for {len(sample_df)} samples")
        # Debug: Print first batch message structure
        print("\nFirst batch message structure:")
        for i in batch_messages[0]:
            for key, value in i.items():
                print(f"{key}: {value}")
            print()

    # Step 5: Run inference
    batch_agent = BatchAsyncLLMAgent(
        api_key=os.getenv('OPENAI_API_KEY'),
        model=model_name,
        temperature=temperature,
    )
    
    async def run_batch():
        # Only pass reasoning_effort for GPT-5 models (gpt-5, gpt-5-mini, gpt-5-nano)
        # GPT-4 models (gpt-4o, gpt-4o-mini, etc.) don't support this parameter
        kwargs = {
            'batch_size': batch_size,
            'max_completion_tokens': max_completion_tokens
        }
        if 'gpt-5' in model_name.lower():
            kwargs['reasoning_effort'] = reasoning_effort

        return await _process_batch_async(
            batch_agent, batch_messages, response_model=response_model,
            **kwargs
        )
    results = asyncio.run(run_batch())

    # Step 6: Merge results
    merged = _merge_ids_with_responses(batch_ids, results)
    df_merged = pd.DataFrame(merged)

    llm_columns = [col for col in df_merged.columns if col not in ['id']]
    df_merged = df_merged.rename(columns={col: f"{col}_llm" for col in llm_columns})

    df_merged['id'] = df_merged['id'].astype(int)
    df_merged = df_merged.merge(sample_df, left_on='id', right_on='index', how='left')
    df_merged = df_merged.dropna(subset=[ground_truth_cols[0]])
    
    # Step 7: Calculate metrics
    if 'agreement' in task_type:
        metrics = _calculate_agreement_metrics(df_merged['agreement_general'], df_merged['agreement_llm'])
    else:
        metrics = _calculate_stance_metrics(df_merged, task_type)

    # Step 8: Display
    print(f"\n{'='*80}")
    print(f"Evaluation: {prompt_key} with {model_name}")
    print(f"Task type: {task_type}, Samples: {len(df_merged)}")
    print(f"{'='*80}\n")

    for key, value in metrics.items():
        if key != 'confusion_matrix' and isinstance(value, (int, float)):
            print(f"{key:30s}: {value:.4f}")

    print(f"\n{'='*80}\n")
    
    if return_dataframe:
        return metrics, df_merged
    else:
        return metrics

# %%
def compare_evaluations(results_dict: dict, sort_by: str = 'accuracy'):
    """
    Compare multiple evaluation results in a table format.
    
    Parameters:
    -----------
    results_dict : dict
        Dictionary with format: {name: metrics_dict}
        Example: {'simple_gpt5': metrics1, 'few_shot_gpt5': metrics2}
    sort_by : str
        Metric to sort by (default: 'accuracy')
    
    Returns:
    --------
    pd.DataFrame
        Comparison table
    """
    comparison_data = []
    
    for name, metrics in results_dict.items():
        row = {'name': name}
        
        # Add relevant metrics (exclude confusion matrix as it's too large)
        for key, value in metrics.items():
            if key != 'confusion_matrix' and isinstance(value, (int, float)):
                row[key] = value
        
        comparison_data.append(row)
    
    df_comparison = pd.DataFrame(comparison_data)
    
    # Sort by specified metric if it exists
    if sort_by in df_comparison.columns:
        df_comparison = df_comparison.sort_values(by=sort_by, ascending=False)
    
    return df_comparison

# %%
def run_batch_evaluation(domain: str, task: str, models=None, variants=None, use_full_dataset=True):
    """
    Run evaluation across multiple models and prompt variants.

    Args:
        domain: 'monetary' or 'fiscal'
        task: 'stance' or 'agreement'
        models: List of models (default: ['gpt-5'])
        variants: List of variants (default: all 4)
        use_full_dataset: Whether to use full dataset or sample (default: True)

    Returns:
        pd.DataFrame: Comparison table of results

    Example:
        run_batch_evaluation('monetary', 'agreement', models=['gpt-5'])
        run_batch_evaluation('fiscal', 'stance', models=['gpt-5', 'gpt-5-mini', 'gpt-5-nano'])
    """
    if models is None:
        models = ['gpt-5']
    if variants is None:
        variants = ['simple', 'with_definitions', 'few_shot', 'chain_of_thought']

    results = {}

    for model in models:
        for variant in variants:
            prompt_key = f'{domain}_{task}_{variant}'
            name = f'{model}_{variant}'

            print(f"\nTesting: {prompt_key} with {model}")
            metrics, _ = evaluate_prompt_and_model(
                prompt_key, model, use_full_dataset=use_full_dataset, return_dataframe=True
            )
            results[name] = metrics

    comparison_df = compare_evaluations(results, sort_by='accuracy')
    print(f"\n{'='*80}")
    print(f"Results: {domain.title()} {task.title()}")
    print(f"{'='*80}\n")
    print(comparison_df.to_string())

    return comparison_df

# %%
def run_comprehensive_evaluation(
    domains=['fiscal','monetary'],
    models=['gpt-4o-2024-08-06'],
    variants=['simple', 'with_definitions', 'few_shot', 'chain_of_thought'],
    use_full_dataset=True,
    save_results=True,
    output_dir='/data/home/xiong/data/Fund/CSR/Tractions/Finetuning_data/eval_results',
    verbose=True
):
    """
    Run comprehensive evaluation across multiple domains, models, and prompt variants.

    Returns: tuple(aggregated_metrics_df, all_result_dfs_dict)
    """
    # Build task list
    tasks = [f'{domain}_{task}' for domain in domains for task in ['agreement', 'stance']]
    total_evaluations = len(tasks) * len(models) * len(variants)

    print(f"\n{'='*100}")
    print(f"Starting Comprehensive Evaluation")
    print(f"Domains: {', '.join(domains)} | Models: {', '.join(models)} | Variants: {', '.join(variants)}")
    print(f"Total evaluations: {total_evaluations}")
    print(f"{'='*100}\n")

    all_results, all_dataframes = {}, {}

    # Run evaluations
    for i, (task, model, variant) in enumerate(
        [(t, m, v) for t in tasks for m in models for v in variants], 1
    ):
        result_name = f'{task}_{model}_{variant}'
        print(f"\n[{i}/{total_evaluations}] {result_name}")

        try:
            metrics, result_df = evaluate_prompt_and_model(
                f'{task}_{variant}', model, use_full_dataset=use_full_dataset,
                return_dataframe=True, verbose=verbose
            )
            all_results[result_name] = metrics
            all_dataframes[result_name] = result_df
            print("✓ Success")
        except Exception as e:
            print(f"✗ Error: {e}")
            all_results[result_name] = all_dataframes[result_name] = None

    # Aggregate metrics
    valid_results = {k: v for k, v in all_results.items() if v is not None}
    if not valid_results:
        print("\n⚠ No valid results to aggregate!")
        return None, None

    aggregated_df = compare_evaluations(valid_results, sort_by='accuracy')

    # Display summary
    print(f"\n{'='*100}")
    print(f"AGGREGATED RESULTS - {' & '.join([d.title() for d in domains])} Evaluation")
    print(f"{'='*100}\n")
    print(aggregated_df.to_string(index=False))
    print(f"\n{'='*100}")
    print(f"Total successful: {len(valid_results)}/{total_evaluations}")
    print(f"{'='*100}\n")

    # Save results
    if save_results:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        domains_str = '_'.join(domains)

        # Save metrics
        aggregated_df.to_csv(output_path / f"{domains_str}_evaluation_metrics.csv", index=False)
        print(f"Metrics saved to: {output_path / f'{domains_str}_evaluation_metrics.csv'}")

        # Save detailed results
        valid_dfs = {k: v for k, v in all_dataframes.items() if v is not None}
        if valid_dfs:
            detailed_dir = output_path / f"{domains_str}_detailed_results"
            detailed_dir.mkdir(parents=True, exist_ok=True)

            for name, df in valid_dfs.items():
                df.to_csv(detailed_dir / f"{name}.csv", index=False)
            print(f"Detailed results saved to: {detailed_dir}/")

            # Save combined predictions
            combined_df = pd.concat([
                df.assign(evaluation_name=name) for name, df in valid_dfs.items()
            ], ignore_index=True)
            combined_df.to_csv(output_path / f"{domains_str}_all_predictions.csv", index=False)
            print(f"Combined predictions saved to: {output_path / f'{domains_str}_all_predictions.csv'}\n")

    return aggregated_df, all_dataframes


# %% Example Usage
if __name__ == "__main__":
    # Example 1: Fiscal only (default - both agreement and stance tasks)
    metrics_df, result_dfs = run_comprehensive_evaluation()

    # Example 2: Both fiscal and monetary
    # df_all = run_comprehensive_evaluation(domains=['fiscal', 'monetary'])

    # Example 3: Monetary only with different models
    # df_monetary = run_comprehensive_evaluation(
    #     domains=['monetary'],
    #     models=['gpt-5', 'gpt-5-mini', 'gpt-5-nano']
    # )

    # Example 4: Quick test with sample data
    # df_test = run_comprehensive_evaluation(
    #     domains=['fiscal'],
    #     use_full_dataset=False
    # )

    # Example 5: Custom configuration
    # df_custom = run_comprehensive_evaluation(
    #     domains=['fiscal', 'monetary'],
    #     models=['gpt-4o'],
    #     variants=['few_shot', 'chain_of_thought'],
    #     use_full_dataset=True
    # )

    # %% Batch Evaluation Examples

    # Example 1: Test all monetary agreement prompts with GPT-5
    # run_batch_evaluation('monetary', 'agreement', models=['gpt-5'])

    # Example 2: Compare models on fiscal stance task
    # run_batch_evaluation('fiscal', 'stance', models=['gpt-5', 'gpt-5-mini', 'gpt-5-nano'])

    # Example 3: Single model, all variants on monetary stance
    # run_batch_evaluation('monetary', 'stance', models=['gpt-5'], use_full_dataset=True)

    # Example 4: Compare specific variants across models
    # run_batch_evaluation('fiscal', 'agreement', models=['gpt-5', 'gpt-5-mini'],
    #                      variants=['few_shot', 'chain_of_thought'])



