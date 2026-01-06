# Monetary Evaluation Results

## Agreement Evaluation

| Model | Prompt Strategy | Accuracy | F1 Score |
|-------|----------------|----------|----------|
| **GPT-4o** | **Simple Short** | **0.7370** | **0.7132** |
| GPT-4o | Simple Long | 0.7093 | 0.6995 |
| GPT-4o | Long with Definition | 0.7232 | 0.7065 |
| GPT-4o | Chain of Thought | 0.7197 | 0.7065 |
| GPT-4o | Few-shot | 0.7232 | 0.7074 |
| GPT-4o-mini | Simple Long | 0.7059 | 0.6647 |
| GPT-3.5-turbo | Simple Long | 0.5536 | 0.5594 |

## Stance Evaluation

### Raw Results

| Model | Prompt Strategy | Current Accuracy | Future Accuracy | Current F1 Score | Future F1 Score |
|-------|----------------|------------------|-----------------|------------------|-----------------|
| GPT-4o | Simple | 0.5882 | **0.6678** | 0.5163 | **0.6547** |
| GPT-4o | With Definition | 0.5900 | 0.6384 | 0.5317 | 0.6297 |
| GPT-4o | Chain of Thought | 0.6021 | 0.6644 | 0.5347 | 0.6495 |
| **GPT-4o** | **Few-shot** | **0.6419** | 0.6609 | **0.6309** | 0.6513 |
| GPT-4o-mini | Simple | 0.5692 | 0.6540 | 0.5091 | 0.6404 |
| GPT-3.5-turbo | Simple | 0.5415 | 0.5536 | 0.5455 | 0.4489 |

### Merging Unclear/Irrelevant

| Model | Prompt Strategy | Current Accuracy | Future Accuracy | Current F1 Score | Future F1 Score |
|-------|----------------|------------------|-----------------|------------------|-----------------|
| GPT-4o | Simple | 0.6436 | **0.7042** | 0.6272 | **0.6998** |
| GPT-4o | With Definition | 0.6228 | 0.6678 | 0.5990 | 0.6647 |
| GPT-4o | Chain of Thought | 0.6471 | 0.6990 | 0.6295 | 0.6969 |
| **GPT-4o** | **Few-shot** | **0.7007** | 0.6972 | **0.7165** | 0.6973 |
| GPT-4o-mini | Simple | 0.5917 | 0.6747 | 0.5563 | 0.6650 |
| GPT-3.5-turbo | Simple | 0.5623 | 0.5606 | 0.5798 | 0.4608 |

---

# Fiscal Evaluation Results

## Agreement Evaluation

| Model | Prompt Strategy | Accuracy | F1 Score |
|-------|----------------|----------|----------|
| GPT-4o | Simple | **0.7000** | 0.6491 |
| GPT-4o | With Definition | **0.7000** | 0.6504 |
| **GPT-4o** | **Chain of Thought** | **0.7000** | **0.6520** |
| GPT-4o | Few-shot | **0.7000** | 0.6442 |
| GPT-4o-mini | Simple | 0.6467 | 0.5731 |
| GPT-3.5-turbo | Simple | 0.5767 | 0.5296 |

## Stance Evaluation

### Raw Results

| Model | Prompt Strategy | Accuracy | F1 Score |
|-------|----------------|----------|----------|
| GPT-4o | Simple | 0.4867 | 0.5454 |
| GPT-4o | With Definition | 0.6150 | 0.6407 |
| **GPT-4o** | **Chain of Thought** | **0.6567** | **0.6565** |
| GPT-4o | Few-shot | 0.5883 | 0.6144 |
| GPT-4o-mini | Simple | 0.5550 | 0.5860 |
| GPT-3.5-turbo | Simple | 0.5867 | 0.5640 |

### Merging Unclear/Irrelevant

| Model | Prompt Strategy | Accuracy | F1 Score |
|-------|----------------|----------|----------|
| **GPT-4o** | **Simple** | **0.7783** | **0.7610** |
| GPT-4o | With Definition | 0.7700 | 0.7549 |
| GPT-4o | Chain of Thought | 0.7617 | 0.7561 |
| GPT-4o | Few-shot | 0.5967 | 0.6262 |
| GPT-4o-mini | Simple | 0.5583 | 0.5910 |
| GPT-3.5-turbo | Simple | 0.5900 | 0.5703 |
