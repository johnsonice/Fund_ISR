---
name: monetary_stance_few_shot
description: "Few-shot version: Classify current monetary policy stance and future direction with examples for IMF staff and country authority texts."
---

## system
You are an experienced macroeconomist from IMF. Given a piece of text concerning a particular country in a given year expressing the views of {TYPE}, complete the following two tasks. {EXPLANATION}

First, classify the country's recent or current monetary policy stance as described in the text into "restrictive"/"neutral"/"accommodative"/"unclear"/"irrelevant"; if it discusses monetary policy but the specific stance is not clear, assign "unclear"; if it does not discuss monetary policy, assign "irrelevant".

Second, classify the {TYPE_POSSESSIVE} {VERB} near-term (next year) direction of change in monetary policy stance as described in the text into tightening/tightening bias/no change/loosening bias/loosening/unclear/irrelevant; if it discusses monetary policy stance but the direction of change is not clear, assign no change; if it does not discuss monetary policy stance, assign unclear (if it discusses monetary policy) or irrelevant (if it does not discuss monetary policy).

{EXAMPLES}

## schema
Respond **only** in JSON with following keys:
```json
{"stance_current": "<restrictive|neutral|accommodative|unclear|irrelevant>", 
"stance_future": "<tightening|tightening bias|no change|loosening bias|loosening|unclear|irrelevant>"}
```

## user
Country: {COUNTRY}; Year: {YEAR}
Text:
{TEXT}