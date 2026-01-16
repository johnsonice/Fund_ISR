import pandas as pd
import pickle
import os
from nltk.tokenize import sent_tokenize, word_tokenize
import nltk
import re
import string
import itertools
import matplotlib.pyplot as plt 
nltk.download('punkt')
import bs4 as bs
import numpy as np
import json
import ast
from functools import reduce
import textstat
from openai import OpenAI
import json
from sklearn.metrics import f1_score, accuracy_score, confusion_matrix, precision_score, recall_score
import seaborn as sn
import random
import tiktoken
from collections import defaultdict
import xlsxwriter


client = OpenAI(api_key="sk-proj-fyoBu7GzQG8H6LEq0lPdT3BlbkFJfZqc0U4ZYoIy89R6I2VP")
plt.rcParams.update({'font.size': 11})
plt.style.use('ggplot')
colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
plt.rcParams['figure.figsize'] = (10,7)
translator = re.compile('[%s]' % re.escape(string.punctuation))

# conventional complexity measures
def textual_complexity(text):
#     ts = time.time()
    # Flesch Reading Ease
    flesch_reading_ease = textstat.flesch_reading_ease(text)

    # Flesch-Kincaid Grade Level
    flesch_kincaid_grade = textstat.flesch_kincaid_grade(text)

    # Gunning Fog Index
    gunning_fog = textstat.gunning_fog(text)

    # Coleman-Liau Index
    coleman_liau_index = textstat.coleman_liau_index(text)

    # SMOG Index
    smog_index = textstat.smog_index(text)

    # Automated Readability Index
    ari = textstat.automated_readability_index(text)

#     print(f"Flesch Reading Ease: {flesch_reading_ease}")
#     print(f"Flesch-Kincaid Grade Level: {flesch_kincaid_grade}")
#     print(f"Gunning Fog Index: {gunning_fog}")
#     print(f"Coleman-Liau Index: {coleman_liau_index}")
#     print(f"SMOG Index: {smog_index}")
#     print(f"Automated Readability Index: {ari}")

    tokens = word_tokenize(text)
    if len(tokens) == 0:
        lexical_diversity = np.nan
        average_sentence_length = np.nan
        number_of_words = 0
    else:
        types = set(tokens)
        lexical_diversity = len(types) / len(tokens)
    #     print(time.time()-ts)

    #     print(f"Lexical Diversity (Type-Token Ratio): {lexical_diversity}")

    # #     nlp = spacy.load('en_core_web_sm')  # Load the English tokenizer, tagger, parser, NER, and word vectors
    #     ts = time.time()
    #     doc = nlp(text)

    #     # Count complex sentences (with more than one clause)
    #     complex_sentences = sum(1 for sent in doc.sents if len(list(sent.ents)) > 1)
    #     print(time.time()-ts)

        # Average sentence length
        average_sentence_length = len(tokens) / len(sent_tokenize(text))

        # number of words
        number_of_words = len(tokens)

    #     print(f"Complex Sentences: {complex_sentences}")
    #     print(f"Average Sentence Length: {average_sentence_length}")
    #     print(time.time()-ts)

    #     return {"Flesch Reading Ease": flesch_reading_ease, "Flesch-Kincaid Grade Level": flesch_kincaid_grade, "Gunning Fog Index": gunning_fog, "Coleman-Liau Index": coleman_liau_index, "SMOG Index": smog_index, "Automated Readability Index": ari, "Lexical Diversity (Type-Token Ratio)": lexical_diversity, "Complex Sentences": complex_sentences, "Average Sentence Length": average_sentence_length}
    return {"Flesch Reading Ease": flesch_reading_ease, "Flesch-Kincaid Grade Level": flesch_kincaid_grade, "Gunning Fog Index": gunning_fog, "Coleman-Liau Index": coleman_liau_index, "SMOG Index": smog_index, "Automated Readability Index": ari, "Lexical Diversity (Type-Token Ratio)": lexical_diversity, "Average Sentence Length": average_sentence_length, "Number of Words": number_of_words}


def check_finetuning_dataset(filepath):
    # Load the dataset
    with open(filepath, 'r', encoding='utf-8') as f:
        dataset = [json.loads(line) for line in f]

    # Initial dataset stats
    print("Num examples:", len(dataset))
    print("First example:")
    for message in dataset[-1]["messages"]:
        print(message)

    # Format error checks
    format_errors = defaultdict(int)

    for ex in dataset:
        if not isinstance(ex, dict):
            format_errors["data_type"] += 1
            continue

        messages = ex.get("messages", None)
        if not messages:
            format_errors["missing_messages_list"] += 1
            continue

        for message in messages:
            if "role" not in message or "content" not in message:
                format_errors["message_missing_key"] += 1

            if any(k not in (
            "role", "content", "name", "function_call", "weight") for k in
                   message):
                format_errors["message_unrecognized_key"] += 1

            if message.get("role", None) not in (
            "system", "user", "assistant", "function"):
                format_errors["unrecognized_role"] += 1

            content = message.get("content", None)
            function_call = message.get("function_call", None)

            if (not content and not function_call) or not isinstance(content,
                                                                     str):
                format_errors["missing_content"] += 1

        if not any(message.get("role", None) == "assistant" for message in
                   messages):
            format_errors["example_missing_assistant_message"] += 1

    if format_errors:
        print("Found errors:")
        for k, v in format_errors.items():
            print(f"{k}: {v}")
    else:
        print("No errors found")


def evaluate(df, model, col, stance=False):
    if stance:
        df[col+'_'+model] = df[col+'_'+model].fillna('')
        rv = {'name': model, 'variable': col,
                'accuracy': accuracy_score(df[col], df[col+'_'+model]),
                'f1_score': f1_score(df[col], df[col+'_'+model], average='weighted'),
              }
#         rv['accuracy_m'] = accuracy_score(df[col].apply(lambda x: 'unclear' if x=='irrelevant' else x), df[col+'_'+model].apply(lambda x: 'unclear' if x=='irrelevant' else x))
#         rv['f1_score_m'] = f1_score(df[col].apply(lambda x: 'unclear' if x=='irrelevant' else x), df[col+'_'+model].apply(lambda x: 'unclear' if x=='irrelevant' else x), average='weighted')

        rv['accuracy_m'] = accuracy_score(df[col].apply(lambda x: 'unclear' if x=='irrelevant' else x.replace(' bias', '')), df[col+'_'+model].apply(lambda x: 'unclear' if x=='irrelevant' else x.replace(' bias', '')))
        rv['f1_score_m'] = f1_score(df[col].apply(lambda x: 'unclear' if x=='irrelevant' else x.replace(' bias', '')), df[col+'_'+model].apply(lambda x: 'unclear' if x=='irrelevant' else x.replace(' bias', '')), average='weighted')

        # rv['accuracy_m'] = accuracy_score(df[col].apply(lambda x: 'unclear' if x=='irrelevant' else 'no change' if 'bias' in x else x), df[col+'_'+model].apply(lambda x: 'unclear' if x=='irrelevant' else 'no change' if 'bias' in x else x))
        # rv['f1_score_m'] = f1_score(df[col].apply(lambda x: 'unclear' if x=='irrelevant' else 'no change' if 'bias' in x else x), df[col+'_'+model].apply(lambda x: 'unclear' if x=='irrelevant' else 'no change' if 'bias' in x else x), average='weighted')

        if col == 'stance_future':
            rv['f1_score_e'] = f1_score(df[col], df[col+'_'+model], average='weighted', labels=['no change', 'tightening bias', 'tightening', 'loosening bias',
       'unclear', 'loosening'])
        else:
            rv['f1_score_e'] = f1_score(df[col], df[col+'_'+model], average='weighted', labels = ['accommodative', 'neutral', 'restrictive'])
    else:
        rv = {'name': model, 'variable': col}
        if 'disagreement_areas' not in col:
            df[col+'_'+model] = df[col+'_'+model].fillna('')
            rv['accuracy'] = accuracy_score(df[col], df[col+'_'+model])
            rv['f1_score'] = f1_score(df[col], df[col+'_'+model], average='weighted')
            rv['accuracy_m'] = accuracy_score(df[col].apply(lambda x: 'mostly agree' if x=='irrelevant' else x), df[col+'_'+model].apply(lambda x: 'mostly agree' if x=='irrelevant' else x))
            rv['f1_score_m'] = f1_score(df[col].apply(lambda x: 'mostly agree' if x=='irrelevant' else x), df[col+'_'+model].apply(lambda x: 'mostly agree' if x=='irrelevant' else x), average='weighted')
            rv['recall'] = recall_score(df[col], df[col+'_'+model], average='weighted', labels=['disagreement exists'])
        else:
            da_vals = list(set(itertools.chain.from_iterable(
                df['disagreement_areas'].apply(
                    lambda x: x.split('; ') if x == x else []))))
            rv['accuracy'] = accuracy_score(df[[col+'_'+v for v in da_vals]], df[[col+'_'+v+'_'+model for v in da_vals]])
            rv['f1_score'] = f1_score(df[[col+'_'+v for v in da_vals]], df[[col+'_'+v+'_'+model for v in da_vals]], average='weighted')
            rv['recall'] = recall_score(df[[col+'_'+v for v in da_vals]], df[[col+'_'+v+'_'+model for v in da_vals]], average='weighted')
    return rv
