###### calculate topic identification accuracy

#%%
import pandas as pd
import ast
#%%

def extract_topic_labels(res_str):
    try:
        res = ast.literal_eval(res_str)
        res = [d['topic_label'] for d in res]
    except:
        res = []
        
    return res
        
    
def extract_and_calculate_accuracy(df, predict_col="topic_labels_processed_1", target_col="ground_truth_label"):
    # Extract key values in the target column
    df['extracted_labels'] = df[predict_col].apply(extract_topic_labels)
    # Check if values in the second target column are in the first target column
    df['is_in_labels'] = df.apply(lambda row: row[target_col] in row['extracted_labels'], axis=1)
    
    # Calculate accuracy rate
    accuracy = df['is_in_labels'].mean()
    return df,accuracy

#%%
if __name__ =="__main__":
    fp = '/root/data/Fund/CSR/llm_detailed_topic_results_gpt-4o-mini.csv'
    df = pd.read_csv(fp)
    #%%
    df,accuracy = extract_and_calculate_accuracy(df,
                                                 predict_col="topic_labels", 
                                                 target_col="ground_truth_label")
    print(accuracy)
    
#%%













