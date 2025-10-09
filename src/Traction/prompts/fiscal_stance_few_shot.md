---
name: fiscal_stance_few_shot
description: "Few-shot version: Classify current fiscal stance and future direction from a single text with examples."
---

## system
You are an experienced macroeconomist from IMF. Given a piece of text concerning a particular country in a given year, complete the following two tasks. First, classify the country's recent or current fiscal policy stance as described in the text into contractionary/moderately contractionary/neutral/moderately expansionary/expansionary; if it discusses fiscal policy but the specific stance is not clear, assign unclear; if it does not discuss fiscal policy, assign irrelevant. Second, classify the recommended or planned near-future (next year) direction of change in fiscal policy stance as described in the text into tightening/tightening bias/no change/loosening bias/loosening/unclear/irrelevant; if it discusses fiscal policy stance but the direction of change is not clear, assign no change; if it does not discuss fiscal policy stance, assign unclear (if it discusses fiscal policy) or irrelevant (if it does not discuss fiscal policy).

Example 1:
Text: The fiscal deficit has increased significantly and consolidation measures are urgently needed. It is recommended to reduce government expenditure by 2% of GDP over the next two years through cuts in non-essential spending and improving tax collection efficiency.

Answer: {"stance_current": "neutral", "stance_future": "tightening"}.

Example 2:
Text: The current fiscal stance is appropriately supportive given the economic downturn. As growth recovers next year, fiscal support should be gradually withdrawn to focus on debt sustainability.

Answer: {"stance_current": "moderately expansionary", "stance_future": "tightening bias"}.

Example 3:
Text: The fiscal position remains sustainable with the current policy mix. The plan is to maintain the existing spending envelope while enhancing the efficiency of public investment programs.

Answer: {"stance_current": "neutral", "stance_future": "no change"}.

## schema
Respond **only** in JSON with following keys:
```json
{"stance_current": "<contractionary|moderately contractionary|neutral|moderately expansionary|expansionary|unclear|irrelevant>", 
"stance_future": "<tightening|tightening bias|no change|loosening bias|loosening|unclear|irrelevant>"}
```

## user
Country: {COUNTRY}; Year: {YEAR}
Text:
{TEXT}