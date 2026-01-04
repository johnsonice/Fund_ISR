# Evaluation Results

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
