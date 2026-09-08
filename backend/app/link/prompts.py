JUDGE_PROMPT = """Compare two grounded facts. Answer JSON:
{{"type": "unrelated"|"corroborates"|"contradicts"|"reconciled",
  "axis": null|"time"|"units"|"scope"|"entity"|"definition",
  "explanation": str, "confidence": number}}
Ask in order: same entity? same metric? same period? same scope/units?
contradicts ONLY if entity+metric+period+scope align and values conflict.
reconciled if it would look like a conflict except time/units/scope/definition.
Write explanation in 2-5 sentences and cite both quotes.
FACT A: {a}
FACT B: {b}
"""
