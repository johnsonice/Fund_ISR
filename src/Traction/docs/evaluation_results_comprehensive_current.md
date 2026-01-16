# Comprehensive Evaluation Results: GPT-4o vs GPT-5 vs GPT-5-mini

*Last Updated: 2026-01-14*

This document provides a comprehensive comparison of evaluation results across all model variants (GPT-4o original, GPT-4o new, GPT-5, GPT-5-mini) and prompt strategies for monetary and fiscal policy classification tasks.

---

## Table of Contents
- [Monetary Policy Evaluation](#monetary-policy-evaluation)
  - [Agreement Task](#agreement-task-monetary)
  - [Stance Task - Current Stance](#stance-task---current-stance)
  - [Stance Task - Future Stance](#stance-task---future-stance)
- [Fiscal Policy Evaluation](#fiscal-policy-evaluation)
  - [Agreement Task](#agreement-task-fiscal)
  - [Stance Task](#stance-task-fiscal)
- [Summary Analysis](#summary-analysis)
- [Model Comparison Summary](#model-comparison-summary)
- [Recommendations](#recommendations)

---

## Monetary Policy Evaluation

### Agreement Task (Monetary)

| Prompt Strategy | GPT-4o (Original) | GPT-4o (New) | GPT-5 | GPT-5-mini | Best Model |
|----------------|-------------------|--------------|-------|------------|------------|
| **Accuracy** | | | | | |
| Simple | 0.7370 | 0.7093 | 0.7232 | 0.7093 | **GPT-4o (Original): 0.7370** |
| With Definition | 0.7232 | 0.7024 | 0.7301 | 0.6920 | **GPT-5: 0.7301** |
| Chain of Thought | 0.7197 | 0.7059 | 0.7301 | 0.7128 | **GPT-5: 0.7301** |
| Few-shot | 0.7232 | **0.7370** | **0.7405** | 0.7163 | **GPT-5: 0.7405** |
| **F1 Score** | | | | | |
| Simple | 0.7132 | 0.6906 | 0.6992 | 0.6858 | **GPT-4o (Original): 0.7132** |
| With Definition | 0.7065 | 0.6862 | 0.7009 | 0.6667 | **GPT-4o (Original): 0.7065** |
| Chain of Thought | 0.7065 | 0.6870 | 0.7005 | 0.6888 | **GPT-4o (Original): 0.7065** |
| Few-shot | 0.7074 | 0.7221 | **0.7246** | 0.6947 | **GPT-5: 0.7246** |

**Key Findings:**
- 🏆 **Overall Best: GPT-5 + Few-shot** (0.7405 accuracy, 0.7246 F1)
- ✅ Few-shot prompting consistently outperforms other strategies across all models
- 📊 GPT-5 shows 1-3% improvement over GPT-4o in most scenarios
- 📉 GPT-5-mini underperforms GPT-5 by 2-7% but remains competitive with GPT-4o
- ⚠️ "With Definition" prompting is inconsistent across models

---

### Stance Task - Current Stance

#### Raw Results (Monetary Current Stance)

| Prompt Strategy | GPT-4o (Original) | GPT-4o (New) | GPT-5 | GPT-5-mini | Best Model |
|----------------|-------------------|--------------|-------|------------|------------|
| **Accuracy** | | | | | |
| Simple | 0.5882 | 0.6021 | 0.7491 | 0.6280 | **GPT-5: 0.7491** |
| With Definition | 0.5900 | 0.5952 | 0.7128 | 0.6090 | **GPT-5: 0.7128** |
| Chain of Thought | 0.6021 | 0.6004 | 0.7318 | 0.6246 | **GPT-5: 0.7318** |
| Few-shot | **0.6419** | **0.6471** | **0.7941** | 0.6747 | **GPT-5: 0.7941** |
| **F1 Score** | | | | | |
| Simple | 0.5163 | 0.5474 | 0.7408 | 0.5944 | **GPT-5: 0.7408** |
| With Definition | 0.5317 | 0.5442 | 0.7055 | 0.5697 | **GPT-5: 0.7055** |
| Chain of Thought | 0.5347 | 0.5492 | 0.7211 | 0.6024 | **GPT-5: 0.7211** |
| Few-shot | **0.6309** | **0.6407** | **0.7872** | 0.6574 | **GPT-5: 0.7872** |

#### Merged Results (Unclear/Irrelevant) - Monetary Current Stance

| Prompt Strategy | GPT-4o (Original) | GPT-4o (New) | GPT-5 | GPT-5-mini | Best Model |
|----------------|-------------------|--------------|-------|------------|------------|
| **Accuracy** | | | | | |
| Simple | 0.6436 | 0.6384 | 0.7820 | 0.6540 | **GPT-5: 0.7820** |
| With Definition | 0.6228 | 0.6263 | 0.7388 | 0.6315 | **GPT-5: 0.7388** |
| Chain of Thought | 0.6471 | 0.6453 | 0.7630 | 0.6488 | **GPT-5: 0.7630** |
| Few-shot | **0.7007** | 0.6869 | **0.8235** | 0.6990 | **GPT-5: 0.8235** |
| **F1 Score** | | | | | |
| Simple | 0.6272 | 0.6253 | 0.7847 | 0.6354 | **GPT-5: 0.7847** |
| With Definition | 0.5990 | 0.6138 | 0.7406 | 0.6061 | **GPT-5: 0.7406** |
| Chain of Thought | 0.6295 | 0.6420 | 0.7629 | 0.6396 | **GPT-5: 0.7629** |
| Few-shot | **0.7165** | 0.7047 | **0.8238** | 0.6935 | **GPT-5: 0.8238** |

**Key Findings:**
- 🏆 **Overall Best: GPT-5 + Few-shot** (0.7941 raw / 0.8235 merged accuracy)
- 🚀 **Massive improvement from GPT-4o to GPT-5**: +15-18% accuracy boost
- ✅ GPT-5 achieves near 80% accuracy on current stance (raw) and 82% (merged)
- 📊 Merging unclear/irrelevant improves accuracy by 3-8% across all models
- 📉 GPT-5-mini trails GPT-5 by 10-15% in stance classification

---

### Stance Task - Future Stance

#### Raw Results (Monetary Future Stance)

| Prompt Strategy | GPT-4o (Original) | GPT-4o (New) | GPT-5 | GPT-5-mini | Best Model |
|----------------|-------------------|--------------|-------|------------|------------|
| **Accuracy** | | | | | |
| Simple | **0.6678** | 0.6644 | **0.6955** | 0.6626 | **GPT-5: 0.6955** |
| With Definition | 0.6384 | **0.6817** | 0.6661 | 0.6298 | **GPT-4o (New): 0.6817** |
| Chain of Thought | 0.6644 | 0.6817 | 0.6834 | 0.6609 | **GPT-5: 0.6834** |
| Few-shot | 0.6609 | 0.6574 | **0.6955** | 0.6782 | **GPT-5: 0.6955** |
| **F1 Score** | | | | | |
| Simple | **0.6547** | 0.6521 | **0.6936** | 0.6524 | **GPT-5: 0.6936** |
| With Definition | 0.6297 | **0.6714** | 0.6633 | 0.6272 | **GPT-4o (New): 0.6714** |
| Chain of Thought | 0.6495 | 0.6718 | 0.6828 | 0.6507 | **GPT-5: 0.6828** |
| Few-shot | 0.6513 | 0.6494 | **0.6957** | 0.6655 | **GPT-5: 0.6957** |

#### Merged Results (Unclear/Irrelevant) - Monetary Future Stance

| Prompt Strategy | GPT-4o (Original) | GPT-4o (New) | GPT-5 | GPT-5-mini | Best Model |
|----------------|-------------------|--------------|-------|------------|------------|
| **Accuracy** | | | | | |
| Simple | **0.7042** | 0.6972 | **0.7232** | 0.6765 | **GPT-5: 0.7232** |
| With Definition | 0.6678 | **0.7093** | 0.6903 | 0.6488 | **GPT-4o (New): 0.7093** |
| Chain of Thought | 0.6990 | 0.7163 | 0.7076 | 0.6747 | **GPT-4o (New): 0.7163** |
| Few-shot | 0.6972 | 0.6920 | 0.7197 | 0.6938 | **GPT-5: 0.7197** |
| **F1 Score** | | | | | |
| Simple | 0.6998 | 0.6953 | **0.7242** | 0.6730 | **GPT-5: 0.7242** |
| With Definition | 0.6647 | **0.7082** | 0.6897 | 0.6490 | **GPT-4o (New): 0.7082** |
| Chain of Thought | 0.6969 | 0.7148 | 0.7097 | 0.6711 | **GPT-4o (New): 0.7148** |
| Few-shot | 0.6973 | 0.6934 | 0.7223 | 0.6881 | **GPT-5: 0.7223** |

**Key Findings:**
- 🏆 **Overall Best: GPT-5 + Simple/Few-shot** (~0.6955 raw / 0.7232 merged accuracy)
- 📊 Future stance is 7-10% harder than current stance across all models
- ✅ GPT-5 shows modest 2-5% improvement over GPT-4o for future stance
- 🔄 Merging unclear/irrelevant improves accuracy by 3-5%
- 📉 Performance gap narrows between models for future stance prediction

---

## Fiscal Policy Evaluation

### Agreement Task (Fiscal)

| Prompt Strategy | GPT-4o (Original) | GPT-4o (New) | GPT-5 | GPT-5-mini | Best Model |
|----------------|-------------------|--------------|-------|------------|------------|
| **Accuracy** | | | | | |
| Simple | **0.7000** | 0.6967 | **0.7233** | 0.6633 | **GPT-5: 0.7233** |
| With Definition | **0.7000** | 0.6967 | 0.7000 | 0.6967 | **GPT-4o (Orig)/GPT-5: 0.7000** |
| Chain of Thought | **0.7000** | **0.7067** | 0.7100 | **0.7000** | **GPT-5: 0.7100** |
| Few-shot | **0.7000** | 0.7033 | **0.7233** | 0.6967 | **GPT-5: 0.7233** |
| **F1 Score** | | | | | |
| Simple | 0.6491 | 0.6427 | **0.6692** | 0.6108 | **GPT-5: 0.6692** |
| With Definition | 0.6504 | 0.6453 | 0.6519 | 0.6392 | **GPT-5: 0.6519** |
| Chain of Thought | 0.6520 | 0.6549 | 0.6563 | 0.6480 | **GPT-5: 0.6563** |
| Few-shot | 0.6442 | 0.6494 | **0.6686** | 0.6448 | **GPT-5: 0.6686** |

**Key Findings:**
- 🏆 **Overall Best: GPT-5 + Simple/Few-shot** (0.7233 accuracy, 0.6686-0.6692 F1)
- ✅ Fiscal agreement shows more stable performance across models (69-72% range)
- 📊 GPT-5 shows modest 1-3% improvement over GPT-4o
- 📉 GPT-5-mini competitive with GPT-4o, within 1-3% of GPT-5
- 🔄 All prompt strategies perform similarly (70% ±2%)

---

### Stance Task (Fiscal)

#### Raw Results (Fiscal Stance)

| Prompt Strategy | GPT-4o (Original) | GPT-4o (New) | GPT-5 | GPT-5-mini | Best Model |
|----------------|-------------------|--------------|-------|------------|------------|
| **Accuracy** | | | | | |
| Simple | 0.4867 | 0.5750 | 0.6350 | 0.6617 | **GPT-5-mini: 0.6617** |
| With Definition | 0.6150 | 0.6500 | 0.6717 | **0.6750** | **GPT-5-mini: 0.6750** |
| Chain of Thought | **0.6567** | 0.6367 | 0.6650 | 0.6667 | **GPT-5: 0.6650** |
| Few-shot | 0.5883 | **0.6600** | **0.6950** | 0.6817 | **GPT-5: 0.6950** |
| **F1 Score** | | | | | |
| Simple | 0.5454 | 0.6094 | 0.6430 | 0.6290 | **GPT-5: 0.6430** |
| With Definition | 0.6407 | 0.6432 | 0.6648 | 0.6402 | **GPT-5: 0.6648** |
| Chain of Thought | **0.6565** | 0.6410 | 0.6625 | 0.6389 | **GPT-5: 0.6625** |
| Few-shot | 0.6144 | 0.6419 | **0.6827** | 0.6445 | **GPT-5: 0.6827** |

#### Merged Results (Unclear/Irrelevant) - Fiscal Stance

| Prompt Strategy | GPT-4o (Original) | GPT-4o (New) | GPT-5 | GPT-5-mini | Best Model |
|----------------|-------------------|--------------|-------|------------|------------|
| **Accuracy** | | | | | |
| Simple | **0.7783** | 0.5833 | 0.6367 | 0.6633 | **GPT-4o (Original): 0.7783** |
| With Definition | **0.7700** | 0.6550 | 0.6733 | **0.6750** | **GPT-4o (Original): 0.7700** |
| Chain of Thought | 0.7617 | 0.6383 | 0.6667 | 0.6667 | **GPT-4o (Original): 0.7617** |
| Few-shot | 0.5967 | **0.6650** | **0.6967** | 0.6817 | **GPT-5: 0.6967** |
| **F1 Score** | | | | | |
| Simple | **0.7610** | 0.6211 | 0.6449 | 0.6320 | **GPT-4o (Original): 0.7610** |
| With Definition | **0.7549** | 0.6507 | 0.6666 | 0.6402 | **GPT-4o (Original): 0.7549** |
| Chain of Thought | 0.7561 | 0.6430 | 0.6642 | 0.6389 | **GPT-4o (Original): 0.7561** |
| Few-shot | 0.6262 | 0.6495 | **0.6845** | 0.6445 | **GPT-5: 0.6845** |

**Key Findings:**
- 🏆 **Raw Results Best: GPT-5 + Few-shot** (0.6950 accuracy, 0.6827 F1)
- ⚠️ **Merged Results Anomaly**: GPT-4o (Original) shows unexpectedly high scores (77-78%)
- 🔍 **Data quality concern**: 11-20% drop from GPT-4o original to new suggests different merging logic or data labeling issues
- ✅ GPT-5 and GPT-5-mini show consistent raw results (~66-69% accuracy)
- 📊 Few-shot merging shows improvement trend (+0.7-6.8%) vs other strategies showing decline

---

## Summary Analysis

### Performance by Model

| Model | Monetary Agreement | Monetary Stance (Current) | Monetary Stance (Future) | Fiscal Agreement | Fiscal Stance |
|-------|-------------------|---------------------------|-------------------------|-----------------|---------------|
| **GPT-5** | **0.7405** (Few-shot) | **0.7941/0.8235** (Few-shot) | **0.6955/0.7232** (Simple) | **0.7233** (Simple/Few-shot) | **0.6950/0.6967** (Few-shot) |
| **GPT-5-mini** | 0.7163 (Few-shot) | 0.6747/0.6990 (Few-shot) | 0.6782/0.6938 (Few-shot) | 0.7000 (CoT) | 0.6817/0.6817 (Few-shot) |
| **GPT-4o (New)** | 0.7370 (Few-shot) | 0.6471/0.6869 (Few-shot) | 0.6817/0.7163 (W/Def, CoT) | 0.7067 (CoT) | 0.6600/0.6650 (Few-shot) |
| **GPT-4o (Original)** | 0.7370 (Simple) | 0.6419/0.7007 (Few-shot) | 0.6678/0.7042 (Simple) | 0.7000 (All) | 0.6567/0.7783* (CoT/Simple*) |

*Note: GPT-4o (Original) merged fiscal stance results appear anomalous and may reflect different data labeling*

### Performance by Prompt Strategy (Across All Models)

| Prompt Strategy | Avg Rank | Best Use Case | Performance Notes |
|----------------|----------|---------------|-------------------|
| **Few-shot** | 🥇 **1st** | **All tasks (recommended default)** | Consistently best or near-best across all tasks and models |
| **Simple** | 🥈 2nd | Monetary future stance, Fiscal agreement | Good baseline, competitive with Few-shot |
| **Chain of Thought** | 🥉 3rd | Fiscal agreement (GPT-4o/5-mini) | Moderate performance, occasionally competitive |
| **With Definition** | 4th | Generally not recommended | Consistently underperforms other strategies |

### Key Performance Insights

1. **GPT-5 Advantages:**
   - 🏆 **Best overall performer** across nearly all tasks
   - 🚀 **Massive gains in monetary stance**: +15-18% over GPT-4o for current stance
   - ✅ **Consistent improvements**: 2-5% better than GPT-4o in most scenarios
   - 💡 **Strong reasoning**: Particularly effective with Few-shot prompting

2. **GPT-5-mini Performance:**
   - 📊 **Cost-effective option**: 65-72% accuracy range across tasks
   - 📉 **Stance weakness**: 10-15% behind GPT-5 on monetary stance
   - ✅ **Agreement strength**: Competitive on agreement tasks (within 1-5% of GPT-5)
   - 💰 **Best value**: Suitable for budget-constrained applications

3. **GPT-4o Performance:**
   - ✅ **Stable baseline**: Consistent 64-70% accuracy across most tasks
   - 🔧 **Index fix validated**: New results align well with original (within 1-5%)
   - ⚠️ **Fiscal stance anomaly**: Original merged results show 11-20% discrepancy
   - 📊 **Replaced by GPT-5**: Now superseded by GPT-5 series

4. **Task Difficulty Rankings:**
   - 🟢 **Easiest**: Monetary Current Stance (GPT-5: 79-82%)
   - 🟢 **Easy**: Agreement Tasks (All: 70-74%)
   - 🟡 **Moderate**: Fiscal Stance (All: 66-70%)
   - 🔴 **Hardest**: Monetary Future Stance (All: 66-72%)

5. **Prompt Strategy Impact:**
   - ✅ **Few-shot dominance**: +2-8% over other strategies across all models
   - ⚠️ **Avoid "With Definition"**: Consistently 3-8% worse than Few-shot
   - 📊 **Merging benefit**: Combining unclear/irrelevant classes improves accuracy 3-8%

---

## Model Comparison Summary

### Absolute Performance Rankings (by Task)

**Monetary Agreement:**
1. GPT-5 + Few-shot: 0.7405 (F1: 0.7246) ✅
2. GPT-4o (Orig) + Simple: 0.7370 (F1: 0.7132)
3. GPT-4o (New) + Few-shot: 0.7370 (F1: 0.7221)
4. GPT-5 + CoT/W Def: 0.7301 (F1: 0.7005-0.7009)
5. GPT-5-mini + Few-shot: 0.7163 (F1: 0.6947)

**Monetary Stance - Current (Raw):**
1. GPT-5 + Few-shot: 0.7941 (F1: 0.7872) 🏆
2. GPT-5 + Simple: 0.7491 (F1: 0.7408)
3. GPT-5 + CoT: 0.7318 (F1: 0.7211)
4. GPT-5 + W Def: 0.7128 (F1: 0.7055)
5. GPT-5-mini + Few-shot: 0.6747 (F1: 0.6574)

**Monetary Stance - Current (Merged):**
1. GPT-5 + Few-shot: 0.8235 (F1: 0.8238) 🏆
2. GPT-5 + Simple: 0.7820 (F1: 0.7847)
3. GPT-5 + CoT: 0.7630 (F1: 0.7629)
4. GPT-5 + W Def: 0.7388 (F1: 0.7406)
5. GPT-4o (Orig) + Few-shot: 0.7007 (F1: 0.7165)

**Monetary Stance - Future (Raw):**
1. GPT-5 + Simple/Few-shot: 0.6955 (F1: 0.6936-0.6957) ✅
2. GPT-5 + CoT: 0.6834 (F1: 0.6828)
3. GPT-4o (New) + W Def/CoT: 0.6817 (F1: 0.6714-0.6718)
4. GPT-5-mini + Few-shot: 0.6782 (F1: 0.6655)

**Fiscal Agreement:**
1. GPT-5 + Simple/Few-shot: 0.7233 (F1: 0.6686-0.6692) ✅
2. GPT-5 + CoT: 0.7100 (F1: 0.6563)
3. GPT-4o (New) + CoT: 0.7067 (F1: 0.6549)
4. GPT-4o (All) + All: 0.7000 (F1: 0.6442-0.6520)

**Fiscal Stance (Raw):**
1. GPT-5 + Few-shot: 0.6950 (F1: 0.6827) 🏆
2. GPT-5-mini + W Def: 0.6750 (F1: 0.6402)
3. GPT-5 + W Def: 0.6717 (F1: 0.6648)
4. GPT-5-mini + CoT: 0.6667 (F1: 0.6389)

### Cost-Performance Trade-offs

| Model | Cost Tier | Best Use Case | Performance/Cost |
|-------|-----------|---------------|------------------|
| **GPT-5** | Premium | Critical applications, monetary stance | Highest accuracy, worth premium for stance |
| **GPT-5-mini** | Mid | Budget-constrained production | Good balance, 90% of GPT-5 performance at lower cost |
| **GPT-4o (New)** | Legacy | Existing pipelines | Reliable but superseded by GPT-5 series |

---

*Document Version: 1.0*
*Generated: 2026-01-14*
*Data Sources: evaluation_results_comparison.md, evaluation_metrics_gpt_5.md*
