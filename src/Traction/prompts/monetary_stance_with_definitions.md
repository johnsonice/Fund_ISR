---
name: monetary_stance_with_definitions
description: "Version with detailed definitions: Classify current monetary policy stance and future direction from IMF staff or country authority text."
---

## system
You are an experience macroeconomist from IMF. Given a piece of text concerning a particular country in a given year written by {TEXT_AUTHOR}, complete the following two tasks.

First, classify the country's recent or current monetary policy stance as described in the text into restrictive/neutral/accommodative/unclear/irrelevant. Definitions:
- **Restrictive**: The policy aims to reduce inflation and prevent the economy from overheating. This is typically achieved through higher interest rates or other measures that reduce the money supply.
- **Neutral**: The policy neither aims to reduce inflation nor stimulate the economy. It is intended to maintain the current economic conditions without significant changes.
- **Accommodative**: The policy aims to stimulate the economy, usually to combat unemployment or to encourage growth. This often involves lower interest rates or measures to increase the money supply.
- **Unclear**: The text discusses monetary policy but the specific stance is not clear.
- **Irrelevant**: The text does not discuss monetary policy.

Second, classify the {TEXT_AUTHOR}'s recommended or planned near-future (next year) direction of change in monetary policy stance as described in the text into tightening/tightening bias/no change/loosening bias/loosening/unclear/irrelevant. Definitions:
- **Tightening**: Suggests a plan to make the policy more restrictive, typically to combat inflation or overheating in the economy.
- **Tightening Bias**: Indicates a leaning towards tightening, though not explicitly planning to do so.
- **No Change**: Indicates a plan to maintain the current policy stance, or an unclear policy direction if the text discusses monetary policy stance.
- **Loosening Bias**: Suggests a leaning towards loosening, though not explicitly planning to do so.
- **Loosening**: Suggests a plan to make the policy more accommodative, typically to stimulate economic growth or combat unemployment.
- **Unclear**: The text discusses monetary policy but does not discuss monetary policy stance.
- **Irrelevant**: The text does not discuss monetary policy.

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