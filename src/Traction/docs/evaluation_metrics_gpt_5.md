# Evaluation Results - V3 Update

*Generated: 2026-01-07*

This report presents evaluation results for GPT-5 and GPT-5-mini models across fiscal and monetary policy classification tasks.

---

# Monetary Evaluation Results

## Agreement Evaluation

| Model | Prompt Strategy | Accuracy | F1 Score |
|-------|----------------|----------|----------|
| **GPT-5** | **Few-shot** | **0.7405** | **0.7246** |
| GPT-5 | Chain of Thought | 0.7301 | 0.7005 |
| GPT-5 | With Definitions | 0.7301 | 0.7009 |
| GPT-5 | Simple | 0.7232 | 0.6992 |
| GPT-5-mini | Few-shot | 0.7163 | 0.6947 |
| GPT-5-mini | Chain of Thought | 0.7128 | 0.6888 |
| GPT-5-mini | Simple | 0.7093 | 0.6858 |
| GPT-5-mini | With Definitions | 0.6920 | 0.6667 |

## Stance Evaluation

### Raw Results

| Model | Prompt Strategy | Current Accuracy | Future Accuracy | Current F1 Score | Future F1 Score |
|-------|----------------|------------------|-----------------|------------------|------------------|
| **GPT-5** | **Few-shot** | **0.7941** | **0.6955** | **0.7872** | **0.6957** |
| **GPT-5** | **Simple** | 0.7491 | **0.6955** | 0.7408 | **0.6936** |
| GPT-5 | Chain of Thought | 0.7318 | 0.6834 | 0.7211 | 0.6828 |
| GPT-5 | With Definitions | 0.7128 | 0.6661 | 0.7055 | 0.6633 |
| GPT-5-mini | Few-shot | 0.6747 | 0.6782 | 0.6574 | 0.6655 |
| GPT-5-mini | Simple | 0.6280 | 0.6626 | 0.5944 | 0.6524 |
| GPT-5-mini | Chain of Thought | 0.6246 | 0.6609 | 0.6024 | 0.6507 |
| GPT-5-mini | With Definitions | 0.6090 | 0.6298 | 0.5697 | 0.6272 |

### Merging Unclear/Irrelevant

| Model | Prompt Strategy | Current Accuracy | Future Accuracy | Current F1 Score | Future F1 Score |
|-------|----------------|------------------|-----------------|------------------|------------------|
| **GPT-5** | **Few-shot** | **0.8235** | 0.7197 | **0.8238** | 0.7223 |
| **GPT-5** | **Simple** | 0.7820 | **0.7232** | 0.7847 | **0.7242** |
| GPT-5 | Chain of Thought | 0.7630 | 0.7076 | 0.7629 | 0.7097 |
| GPT-5 | With Definitions | 0.7388 | 0.6903 | 0.7406 | 0.6897 |
| GPT-5-mini | Few-shot | 0.6990 | 0.6938 | 0.6935 | 0.6881 |
| GPT-5-mini | Simple | 0.6540 | 0.6765 | 0.6354 | 0.6730 |
| GPT-5-mini | Chain of Thought | 0.6488 | 0.6747 | 0.6396 | 0.6711 |
| GPT-5-mini | With Definitions | 0.6315 | 0.6488 | 0.6061 | 0.6490 |

---

# Fiscal Evaluation Results

## Agreement Evaluation

| Model | Prompt Strategy | Accuracy | F1 Score |
|-------|----------------|----------|----------|
| **GPT-5** | **Simple** | **0.7233** | **0.6692** |
| **GPT-5** | **Few-shot** | **0.7233** | **0.6686** |
| GPT-5 | Chain of Thought | 0.7100 | 0.6563 |
| GPT-5-mini | Chain of Thought | 0.7000 | 0.6480 |
| GPT-5 | With Definitions | 0.7000 | 0.6519 |
| GPT-5-mini | Few-shot | 0.6967 | 0.6448 |
| GPT-5-mini | With Definitions | 0.6967 | 0.6392 |
| GPT-5-mini | Simple | 0.6633 | 0.6108 |

## Stance Evaluation

### Raw Results

| Model | Prompt Strategy | Accuracy | F1 Score |
|-------|----------------|----------|----------|
| **GPT-5** | **Few-shot** | **0.6950** | **0.6827** |
| GPT-5-mini | Few-shot | 0.6817 | 0.6445 |
| GPT-5-mini | With Definitions | 0.6750 | 0.6402 |
| GPT-5 | With Definitions | 0.6717 | 0.6648 |
| GPT-5-mini | Chain of Thought | 0.6667 | 0.6389 |
| GPT-5 | Chain of Thought | 0.6650 | 0.6625 |
| GPT-5-mini | Simple | 0.6617 | 0.6290 |
| GPT-5 | Simple | 0.6350 | 0.6430 |

### Merging Unclear/Irrelevant

| Model | Prompt Strategy | Accuracy | F1 Score |
|-------|----------------|----------|----------|
| **GPT-5** | **Few-shot** | **0.6967** | **0.6845** |
| GPT-5-mini | Few-shot | 0.6817 | 0.6445 |
| GPT-5-mini | With Definitions | 0.6750 | 0.6402 |
| GPT-5 | With Definitions | 0.6733 | 0.6666 |
| GPT-5-mini | Chain of Thought | 0.6667 | 0.6389 |
| GPT-5 | Chain of Thought | 0.6667 | 0.6642 |
| GPT-5-mini | Simple | 0.6633 | 0.6320 |
| GPT-5 | Simple | 0.6367 | 0.6449 |

