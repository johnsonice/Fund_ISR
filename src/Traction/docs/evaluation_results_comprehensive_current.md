# Comprehensive Evaluation Results: GPT-4o vs GPT-5 vs GPT-5-mini vs GPT-4.1 Fine-tuned

*Last Updated: 2026-01-27*

---

## Monetary Policy Evaluation

### Agreement Task (Monetary)

| Prompt Strategy | GPT-4o (Original) | GPT-4o (New) | GPT-5 | GPT-5-mini | GPT-4.1 Fine-tuned | Best Model |
|----------------|-------------------|--------------|-------|------------|-------------------|------------|
| **Accuracy** | | | | | | |
| Simple | 0.7370 | 0.7093 | 0.7232 | 0.7093 | **0.7759** | **GPT-4.1 FT: 0.7759** |
| With Definition | 0.7232 | 0.7024 | 0.7301 | 0.6920 | - | **GPT-5: 0.7301** |
| Chain of Thought | 0.7197 | 0.7059 | 0.7301 | 0.7128 | - | **GPT-5: 0.7301** |
| Few-shot | 0.7232 | **0.7370** | **0.7405** | 0.7163 | - | **GPT-5: 0.7405** |
| **F1 Score** | | | | | | |
| Simple | 0.7132 | 0.6906 | 0.6992 | 0.6858 | **0.7333** | **GPT-4.1 FT: 0.7333** |
| With Definition | 0.7065 | 0.6862 | 0.7009 | 0.6667 | - | **GPT-4o (Original): 0.7065** |
| Chain of Thought | 0.7065 | 0.6870 | 0.7005 | 0.6888 | - | **GPT-4o (Original): 0.7065** |
| Few-shot | 0.7074 | 0.7221 | **0.7246** | 0.6947 | - | **GPT-5: 0.7246** |

---

### Stance Task - Current Stance

#### Raw Results (Monetary Current Stance)

| Prompt Strategy | GPT-4o (Original) | GPT-4o (New) | GPT-5 | GPT-5-mini | GPT-4.1 Fine-tuned | Best Model |
|----------------|-------------------|--------------|-------|------------|-------------------|------------|
| **Accuracy** | | | | | | |
| Simple | 0.5882 | 0.6021 | 0.7491 | 0.6280 | **0.8362** | **GPT-4.1 FT: 0.8362** |
| With Definition | 0.5900 | 0.5952 | 0.7128 | 0.6090 | - | **GPT-5: 0.7128** |
| Chain of Thought | 0.6021 | 0.6004 | 0.7318 | 0.6246 | - | **GPT-5: 0.7318** |
| Few-shot | **0.6419** | **0.6471** | **0.7941** | 0.6747 | - | **GPT-5: 0.7941** |
| **F1 Score** | | | | | | |
| Simple | 0.5163 | 0.5474 | 0.7408 | 0.5944 | **0.8390** | **GPT-4.1 FT: 0.8390** |
| With Definition | 0.5317 | 0.5442 | 0.7055 | 0.5697 | - | **GPT-5: 0.7055** |
| Chain of Thought | 0.5347 | 0.5492 | 0.7211 | 0.6024 | - | **GPT-5: 0.7211** |
| Few-shot | **0.6309** | **0.6407** | **0.7872** | 0.6574 | - | **GPT-5: 0.7872** |

#### Merged Results (Unclear/Irrelevant) - Monetary Current Stance

| Prompt Strategy | GPT-4o (Original) | GPT-4o (New) | GPT-5 | GPT-5-mini | GPT-4.1 Fine-tuned | Best Model |
|----------------|-------------------|--------------|-------|------------|-------------------|------------|
| **Accuracy** | | | | | | |
| Simple | 0.6436 | 0.6384 | 0.7820 | 0.6540 | **0.8362** | **GPT-4.1 FT: 0.8362** |
| With Definition | 0.6228 | 0.6263 | 0.7388 | 0.6315 | - | **GPT-5: 0.7388** |
| Chain of Thought | 0.6471 | 0.6453 | 0.7630 | 0.6488 | - | **GPT-5: 0.7630** |
| Few-shot | **0.7007** | 0.6869 | **0.8235** | 0.6990 | - | **GPT-5: 0.8235** |
| **F1 Score** | | | | | | |
| Simple | 0.6272 | 0.6253 | 0.7847 | 0.6354 | **0.8387** | **GPT-4.1 FT: 0.8387** |
| With Definition | 0.5990 | 0.6138 | 0.7406 | 0.6061 | - | **GPT-5: 0.7406** |
| Chain of Thought | 0.6295 | 0.6420 | 0.7629 | 0.6396 | - | **GPT-5: 0.7629** |
| Few-shot | **0.7165** | 0.7047 | **0.8238** | 0.6935 | - | **GPT-5: 0.8238** |

---

### Stance Task - Future Stance

#### Raw Results (Monetary Future Stance)

| Prompt Strategy | GPT-4o (Original) | GPT-4o (New) | GPT-5 | GPT-5-mini | GPT-4.1 Fine-tuned | Best Model |
|----------------|-------------------|--------------|-------|------------|-------------------|------------|
| **Accuracy** | | | | | | |
| Simple | **0.6678** | 0.6644 | **0.6955** | 0.6626 | **0.7414** | **GPT-4.1 FT: 0.7414** |
| With Definition | 0.6384 | **0.6817** | 0.6661 | 0.6298 | - | **GPT-4o (New): 0.6817** |
| Chain of Thought | 0.6644 | 0.6817 | 0.6834 | 0.6609 | - | **GPT-5: 0.6834** |
| Few-shot | 0.6609 | 0.6574 | **0.6955** | 0.6782 | - | **GPT-5: 0.6955** |
| **F1 Score** | | | | | | |
| Simple | **0.6547** | 0.6521 | **0.6936** | 0.6524 | **0.7422** | **GPT-4.1 FT: 0.7422** |
| With Definition | 0.6297 | **0.6714** | 0.6633 | 0.6272 | - | **GPT-4o (New): 0.6714** |
| Chain of Thought | 0.6495 | 0.6718 | 0.6828 | 0.6507 | - | **GPT-5: 0.6828** |
| Few-shot | 0.6513 | 0.6494 | **0.6957** | 0.6655 | - | **GPT-5: 0.6957** |

#### Merged Results (Unclear/Irrelevant) - Monetary Future Stance

| Prompt Strategy | GPT-4o (Original) | GPT-4o (New) | GPT-5 | GPT-5-mini | GPT-4.1 Fine-tuned | Best Model |
|----------------|-------------------|--------------|-------|------------|-------------------|------------|
| **Accuracy** | | | | | | |
| Simple | **0.7042** | 0.6972 | **0.7232** | 0.6765 | **0.7414** | **GPT-4.1 FT: 0.7414** |
| With Definition | 0.6678 | **0.7093** | 0.6903 | 0.6488 | - | **GPT-4o (New): 0.7093** |
| Chain of Thought | 0.6990 | 0.7163 | 0.7076 | 0.6747 | - | **GPT-4o (New): 0.7163** |
| Few-shot | 0.6972 | 0.6920 | 0.7197 | 0.6938 | - | **GPT-5: 0.7197** |
| **F1 Score** | | | | | | |
| Simple | 0.6998 | 0.6953 | **0.7242** | 0.6730 | **0.7419** | **GPT-4.1 FT: 0.7419** |
| With Definition | 0.6647 | **0.7082** | 0.6897 | 0.6490 | - | **GPT-4o (New): 0.7082** |
| Chain of Thought | 0.6969 | 0.7148 | 0.7097 | 0.6711 | - | **GPT-4o (New): 0.7148** |
| Few-shot | 0.6973 | 0.6934 | 0.7223 | 0.6881 | - | **GPT-5: 0.7223** |

---

## Fiscal Policy Evaluation

### Agreement Task (Fiscal)

| Prompt Strategy | GPT-4o (Original) | GPT-4o (New) | GPT-5 | GPT-5-mini | GPT-4.1 Fine-tuned | Best Model |
|----------------|-------------------|--------------|-------|------------|-------------------|------------|
| **Accuracy** | | | | | | |
| Simple | **0.7000** | 0.6967 | **0.7233** | 0.6633 | **0.8000** | **GPT-4.1 FT: 0.8000** |
| With Definition | **0.7000** | 0.6967 | 0.7000 | 0.6967 | - | **GPT-4o (Orig)/GPT-5: 0.7000** |
| Chain of Thought | **0.7000** | **0.7067** | 0.7100 | **0.7000** | - | **GPT-5: 0.7100** |
| Few-shot | **0.7000** | 0.7033 | **0.7233** | 0.6967 | - | **GPT-5: 0.7233** |
| **F1 Score** | | | | | | |
| Simple | 0.6491 | 0.6427 | **0.6692** | 0.6108 | **0.7866** | **GPT-4.1 FT: 0.7866** |
| With Definition | 0.6504 | 0.6453 | 0.6519 | 0.6392 | - | **GPT-5: 0.6519** |
| Chain of Thought | 0.6520 | 0.6549 | 0.6563 | 0.6480 | - | **GPT-5: 0.6563** |
| Few-shot | 0.6442 | 0.6494 | **0.6686** | 0.6448 | - | **GPT-5: 0.6686** |

---

### Stance Task (Fiscal)

#### Raw Results (Fiscal Stance)

| Prompt Strategy | GPT-4o (Original) | GPT-4o (New) | GPT-5 | GPT-5-mini | GPT-4.1 Fine-tuned | Best Model |
|----------------|-------------------|--------------|-------|------------|-------------------|------------|
| **Accuracy** | | | | | | |
| Simple | 0.4867 | 0.5750 | 0.6350 | 0.6617 | **0.7417** | **GPT-4.1 FT: 0.7417** |
| With Definition | 0.6150 | 0.6500 | 0.6717 | **0.6750** | - | **GPT-5-mini: 0.6750** |
| Chain of Thought | **0.6567** | 0.6367 | 0.6650 | 0.6667 | - | **GPT-5: 0.6650** |
| Few-shot | 0.5883 | **0.6600** | **0.6950** | 0.6817 | - | **GPT-5: 0.6950** |
| **F1 Score** | | | | | | |
| Simple | 0.5454 | 0.6094 | 0.6430 | 0.6290 | **0.6987** | **GPT-4.1 FT: 0.6987** |
| With Definition | 0.6407 | 0.6432 | 0.6648 | 0.6402 | - | **GPT-5: 0.6648** |
| Chain of Thought | **0.6565** | 0.6410 | 0.6625 | 0.6389 | - | **GPT-5: 0.6625** |
| Few-shot | 0.6144 | 0.6419 | **0.6827** | 0.6445 | - | **GPT-5: 0.6827** |

#### Merged Results (Unclear/Irrelevant) - Fiscal Stance

| Prompt Strategy | GPT-4o (Original) | GPT-4o (New) | GPT-5 | GPT-5-mini | GPT-4.1 Fine-tuned | Best Model |
|----------------|-------------------|--------------|-------|------------|-------------------|------------|
| **Accuracy** | | | | | | |
| Simple | **0.7783** | 0.5833 | 0.6367 | 0.6633 | **0.7417** | **GPT-4o (Original): 0.7783** |
| With Definition | **0.7700** | 0.6550 | 0.6733 | **0.6750** | - | **GPT-4o (Original): 0.7700** |
| Chain of Thought | 0.7617 | 0.6383 | 0.6667 | 0.6667 | - | **GPT-4o (Original): 0.7617** |
| Few-shot | 0.5967 | **0.6650** | **0.6967** | 0.6817 | - | **GPT-5: 0.6967** |
| **F1 Score** | | | | | | |
| Simple | **0.7610** | 0.6211 | 0.6449 | 0.6320 | **0.6987** | **GPT-4o (Original): 0.7610** |
| With Definition | **0.7549** | 0.6507 | 0.6666 | 0.6402 | - | **GPT-4o (Original): 0.7549** |
| Chain of Thought | 0.7561 | 0.6430 | 0.6642 | 0.6389 | - | **GPT-4o (Original): 0.7561** |
| Few-shot | 0.6262 | 0.6495 | **0.6845** | 0.6445 | - | **GPT-5: 0.6845** |

---

## Summary

### Performance by Model (Best Results per Task)

| Model | Monetary Agreement | Monetary Stance (Current) | Monetary Stance (Future) | Fiscal Agreement | Fiscal Stance |
|-------|-------------------|---------------------------|-------------------------|-----------------|---------------|
| **GPT-4.1 Fine-tuned** | **0.7759** (Simple) | **0.8362/0.8362** (Simple) | **0.7414/0.7414** (Simple) | **0.8000** (Simple) | **0.7417/0.7417** (Simple) |
| **GPT-5** | 0.7405 (Few-shot) | 0.7941/0.8235 (Few-shot) | 0.6955/0.7232 (Simple) | 0.7233 (Simple/Few-shot) | 0.6950/0.6967 (Few-shot) |
| **GPT-5-mini** | 0.7163 (Few-shot) | 0.6747/0.6990 (Few-shot) | 0.6782/0.6938 (Few-shot) | 0.7000 (CoT) | 0.6817/0.6817 (Few-shot) |
| **GPT-4o (New)** | 0.7370 (Few-shot) | 0.6471/0.6869 (Few-shot) | 0.6817/0.7163 (W/Def, CoT) | 0.7067 (CoT) | 0.6600/0.6650 (Few-shot) |
| **GPT-4o (Original)** | 0.7370 (Simple) | 0.6419/0.7007 (Few-shot) | 0.6678/0.7042 (Simple) | 0.7000 (All) | 0.6567/0.7783* (CoT/Simple*) |

*Note: GPT-4o (Original) merged fiscal stance results appear anomalous and may reflect different data labeling*

*Note: GPT-4.1 Fine-tuned models use Simple prompt only. Stance values show Raw/Merged accuracy.*

---

*Document Version: 2.0*
*Generated: 2026-01-27*
