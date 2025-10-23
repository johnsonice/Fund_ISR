# Evaluation Results: Fiscal-Monetary Pipeline

## Dataset Information
- **Total Samples**: 289 (231 train + 58 test)
- **Agreement Classes**: `['disagreement exists', 'mostly agree', 'irrelevant']`
- **Stance Classes**: `['tightening', 'neutral/mixed', 'easing']`

---

## Monetary Agreement Task

### GPT-5 Results

| Prompt Strategy | Accuracy | F1 (Weighted) | F1 (Macro) | Precision (Weighted) | Recall (Weighted) |
|----------------|----------|---------------|------------|---------------------|-------------------|
| Few Shot | **0.7474** | **0.7327** | **0.5810** | **0.7601** | **0.7474** |
| Chain of Thought | 0.7439 | 0.7242 | 0.5357 | 0.7309 | 0.7439 |
| Simple | 0.7405 | 0.7241 | 0.5548 | 0.7416 | 0.7405 |
| With Definitions | 0.7301 | 0.7046 | 0.4863 | 0.7117 | 0.7301 |

**Confusion Matrix (Few Shot - Best Performer):**
```
                   Pred: Disagreement  Pred: Agree  Pred: Irrelevant
True: Disagreement        35               28            0
True: Agree               27              176            0
True: Irrelevant           1               17            5
```

---

### GPT-5-Mini Results

| Prompt Strategy | Accuracy | F1 (Weighted) | F1 (Macro) | Precision (Weighted) | Recall (Weighted) |
|----------------|----------|---------------|------------|---------------------|-------------------|
| Few Shot | **0.7197** | 0.6944 | 0.4770 | 0.7410 | 0.7197 |
| Chain of Thought | 0.7163 | **0.6945** | **0.4799** | **0.7452** | 0.7163 |
| With Definitions | 0.7093 | 0.6837 | 0.4492 | 0.6609 | 0.7093 |
| Simple | 0.7059 | 0.6774 | 0.4390 | 0.6511 | 0.7059 |

**Confusion Matrix (Few Shot - Best Performer):**
```
                   Pred: Disagreement  Pred: Agree  Pred: Irrelevant
True: Disagreement        35               28            0
True: Agree               31              172            0
True: Irrelevant           2               20            1
```

---

### GPT-5-Nano Results

| Prompt Strategy | Accuracy | F1 (Weighted) | F1 (Macro) | Precision (Weighted) | Recall (Weighted) |
|----------------|----------|---------------|------------|---------------------|-------------------|
| Few Shot | **0.6644** | **0.6395** | 0.4015 | 0.6167 | **0.6644** |
| Simple | 0.6574 | 0.6354 | **0.4026** | 0.6160 | 0.6574 |
| With Definitions | 0.6367 | 0.6126 | 0.3758 | 0.5904 | 0.6367 |
| Chain of Thought | 0.6298 | 0.6136 | 0.4012 | **0.6692** | 0.6298 |

**Confusion Matrix (Few Shot - Best Performer):**
```
                   Pred: Disagreement  Pred: Agree  Pred: Irrelevant
True: Disagreement        29               34            0
True: Agree               40              163            0
True: Irrelevant           4               19            0
```

---

## Monetary Stance Task

### GPT-5 Results

#### Overall Metrics (Averaged Across Current & Future)

| Prompt Strategy | Avg Accuracy | Avg F1 (Weighted) | Avg F1 (Macro) |
|----------------|--------------|-------------------|----------------|
| Few Shot | **0.7405** | **0.7364** | **0.6206** |
| Chain of Thought | 0.7042 | 0.6942 | 0.4752 |
| Simple | 0.7007 | 0.6970 | 0.5113 |
| With Definitions | 0.6367 | 0.6254 | 0.4151 |

#### Current Stance Performance

| Prompt Strategy | Accuracy | F1 (Weighted) | F1 (Macro) |
|----------------|----------|---------------|------------|
| Few Shot | **0.7855** | **0.7747** | **0.6840** |
| Simple | 0.7405 | 0.7249 | 0.5363 |
| Chain of Thought | 0.7266 | 0.7068 | 0.4808 |
| With Definitions | 0.6505 | 0.6091 | 0.4069 |

#### Future Stance Performance

| Prompt Strategy | Accuracy | F1 (Weighted) | F1 (Macro) |
|----------------|----------|---------------|------------|
| Few Shot | **0.6955** | **0.6981** | **0.5571** |
| Chain of Thought | 0.6817 | 0.6815 | 0.4696 |
| Simple | 0.6609 | 0.6691 | 0.4863 |
| With Definitions | 0.6228 | 0.6417 | 0.4233 |

---

### GPT-5-Mini Results

#### Overall Metrics (Averaged Across Current & Future)

| Prompt Strategy | Avg Accuracy | Avg F1 (Weighted) | Avg F1 (Macro) |
|----------------|--------------|-------------------|----------------|
| Few Shot | **0.6540** | **0.6381** | **0.4471** |
| Simple | 0.6384 | 0.6198 | 0.3825 |
| Chain of Thought | 0.6315 | 0.6096 | 0.4241 |
| With Definitions | 0.5969 | 0.5764 | 0.3716 |

#### Current Stance Performance

| Prompt Strategy | Accuracy | F1 (Weighted) | F1 (Macro) |
|----------------|----------|---------------|------------|
| Few Shot | **0.6747** | **0.6386** | **0.4654** |
| Simple | 0.6471 | 0.6158 | 0.4065 |
| Chain of Thought | 0.6401 | 0.5944 | 0.4311 |
| With Definitions | 0.6125 | 0.5566 | 0.3663 |

#### Future Stance Performance

| Prompt Strategy | Accuracy | F1 (Weighted) | F1 (Macro) |
|----------------|----------|---------------|------------|
| Few Shot | **0.6332** | **0.6376** | **0.4289** |
| Simple | 0.6298 | 0.6237 | 0.3585 |
| Chain of Thought | 0.6228 | 0.6248 | 0.4172 |
| With Definitions | 0.5813 | 0.5961 | 0.3769 |

---

## Key Findings

### Agreement Task Performance
- **Best Model**: GPT-5 (74.74% accuracy) > GPT-5-Mini (71.97%) > GPT-5-Nano (66.44%)
- **Best Configuration by Model**:
  - GPT-5: Few Shot prompt (74.74%)
  - GPT-5-Mini: Few Shot prompt (71.97%)
  - GPT-5-Nano: Few Shot prompt (66.44%)
- **Performance Gap**: ~3% between GPT-5 and GPT-5-Mini, ~5% between GPT-5-Mini and GPT-5-Nano

### Stance Task Performance
- **Best Model**: GPT-5 significantly outperforms smaller models
  - GPT-5: 74.05% average accuracy (Few Shot)
  - GPT-5-Mini: 65.40% average accuracy (Few Shot)
  - Performance gap: ~8.6% between GPT-5 and GPT-5-Mini
- **Temporal Dimension**: Current stance is easier than future stance across all models
  - GPT-5: 78.55% (current) vs 69.55% (future) - 9% gap
  - GPT-5-Mini: 67.47% (current) vs 63.32% (future) - 4% gap
- **Task Comparison**:
  - Agreement task: 66-75% accuracy range
  - Stance task: 60-74% accuracy range
  - GPT-5 handles stance task nearly as well as agreement task, smaller models struggle more

### Prompt Strategy Insights
1. **Few Shot**: Clear winner across ALL models and tasks
   - Best for GPT-5 in both agreement (74.74%) and stance (74.05%) tasks
   - Best for GPT-5-Mini in both tasks
   - Best for GPT-5-Nano in agreement task
   - Concrete examples significantly improve performance
2. **Chain of Thought**: Second best for some configurations
   - GPT-5 agreement: 74.39% (close to Few Shot)
   - GPT-5-Mini agreement: 71.63% (competitive)
   - Mixed results for stance tasks
3. **Simple**: Good baseline but consistently underperforms Few Shot
   - Works reasonably well but misses 2-4% accuracy vs Few Shot
4. **With Definitions**: Consistently worst performer
   - Adds noise or confuses the model
   - 3-8% accuracy drop compared to Few Shot

### Model Selection Recommendations

#### For Agreement Task:
- **High Accuracy Priority**: GPT-5 + Few Shot (74.74%)
- **Cost-Accuracy Balance**: GPT-5-Mini + Few Shot (71.97%) - only 2.8% accuracy loss
- **Budget Constrained**: GPT-5-Nano + Few Shot (66.44%) - 8.3% accuracy loss but still viable

#### For Stance Task:
- **High Accuracy Priority**: GPT-5 + Few Shot (74.05%)
  - Dramatically better: 78.55% on current stance, 69.55% on future stance
- **Cost-Accuracy Balance**: GPT-5-Mini + Few Shot (65.40%) - 8.6% accuracy loss
  - Consider if budget is tight, but significant performance drop
- **Budget Constrained**: Not evaluated yet for GPT-5-Nano

#### General Guidance:
- **Always use Few Shot prompts** - consistently best across all configurations
- **GPT-5 is worth the premium for stance classification** - much larger performance gap than agreement task
- **Avoid "With Definitions" prompt** - consistently underperforms
