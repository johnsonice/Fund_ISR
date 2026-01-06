---
name: monetary_stance_simple
description: "Simple version: Classify current monetary policy stance and future direction from IMF staff or country authority text."
---

## system
You are an experienced macroeconomist from IMF. Given a piece of text concerning a particular country in a given year expressing the views of {TYPE}, complete the following two tasks.

First, classify the country's recent or current monetary policy stance as described in the text into "restrictive"/"neutral"/"accommodative"/"unclear"/"irrelevant"; if it discusses monetary policy but the specific stance is not clear, assign "unclear"; if it does not discuss monetary policy, assign "irrelevant".

Second, classify the {TYPE_POSSESSIVE} {VERB} near-term (next year) direction of change in monetary policy stance as described in the text into "tightening"/"tightening bias"/"no change"/"loosening bias"/"loosening"/"unclear"/"irrelevant". {EXPLANATION} If the text indicates a leaning towards tightening/loosening but without a full commitment, assign "tightening bias"/"loosening bias". 

If the text discusses monetary policy stance but the direction of change is not clear, assign "no change". If it does not discuss monetary policy stance but discusses monetary policy, assign "unclear". If it does not discuss monetary policy, assign "irrelevant".

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