#!/usr/bin/env python3
"""TD 2 (Pair C): routing simulator adapted to the sub-group's routing rule.

Synthetic decisions, no API call, no key. The original supplied version is kept
in reports/td2-evidence/atelier-routage-original.py and its output in
reports/td2-evidence/routage-avant.jsonl.

What changed compared with the supplied simulator:
- RESOURCES are the five TD 1 models (free routes actually used in TD 1) plus
  the paid OpenRouter routes of the same models, priced from
  portefeuille-modeles-2026-09-28.csv / five-model-summary-en.csv.
- Eligibility is no longer a single "level": each resource lists the question
  families on which it was 100 % correct in TD 1, with the cells as evidence
  (model-question-comparison-en.csv). A combined family is eligible only if the
  model is 100 % on the combination AND on each of its component families.
- The checking depends on the family and on the use (dashboard, customer,
  payout), as written in the routing rule of reports/td2.md.
- The priority order of choose() is unchanged: included capacity, then
  deferral to a free route that refills before the deadline, then a paid route
  within the budget, then abstention.

Costs are USD excluding tax per request, estimated with the mean TD 1 token
envelope of each model (prompt about 640 tokens, completion 130 to 240 tokens).
Quota availability is supplied as a scenario, not measured from a provider.
"""
import argparse
import json

# Families of questions-td1.json and the TD 1 cells that belong to each one.
FAMILIES = {
    "F1": ["C01", "C04", "C05", "C06", "C07", "C20"],       # period
    "F2": ["C02", "C08", "C09", "C11"],                      # age on a reference date
    "F2b": ["C10"],                                          # age at the time of the order
    "F3": ["C03", "C12", "C13", "C14"],                      # product list
    "F1+F2": ["C15"],
    "F2+F3": ["C16"],
    "F1+F2+F3": ["C17", "C19"],
    "F1+F2b": ["C18"],
}

# TD 1 evidence per model: family -> "correct/cases (failed cells)".
TD1 = {
    "gpt-oss-120b": {"F1": "6/6", "F2": "4/4", "F2b": "1/1", "F3": "4/4", "F1+F2": "1/1",
                     "F2+F3": "1/1", "F1+F2+F3": "2/2", "F1+F2b": "1/1"},
    "gpt-oss-20b": {"F1": "6/6", "F2": "1/4 (C02, C09, C11 incorrect)", "F2b": "1/1", "F3": "4/4",
                    "F1+F2": "1/1", "F2+F3": "1/1", "F1+F2+F3": "2/2", "F1+F2b": "1/1"},
    "north-mini-code": {"F1": "6/6", "F2": "0/4 (C02, C09 sql_invalid; C08, C11 incorrect)",
                        "F2b": "0/1 (C10 incorrect)", "F3": "4/4", "F1+F2": "0/1 (C15)",
                        "F2+F3": "0/1 (C16)", "F1+F2+F3": "0/2 (C17, C19)", "F1+F2b": "1/1"},
    "qwen3.8-27b": {"F1": "6/6", "F2": "3/4 (C09 incorrect)", "F2b": "0/1 (C10 incorrect)",
                    "F3": "4/4", "F1+F2": "0/1 (C15)", "F2+F3": "0/1 (C16)",
                    "F1+F2+F3": "0/2 (C17, C19)", "F1+F2b": "0/1 (C18 not executed, HTTP 429)"},
    "dots-3-note-preview": {"F1": "6/6", "F2": "2/4 (C02, C09 incorrect)", "F2b": "0/1 (C10)",
                            "F3": "4/4", "F1+F2": "1/1", "F2+F3": "1/1",
                            "F1+F2+F3": "0/2 (C17 incorrect, C19 sql_invalid)",
                            "F1+F2b": "0/1 (C18 incorrect)"},
}


def eligible_families(model):
    """Families where the model is 100 % in TD 1, combinations included only if
    every component family is also 100 % (a 1/1 cell alone is weak evidence)."""
    perfect = {f for f, r in TD1[model].items() if r.split()[0].split("/")[0] == r.split()[0].split("/")[1]}
    return sorted(f for f in perfect if all(part in perfect for part in f.split("+")))


def resource(rid, model, access, cash, allocation=0.0, available=True, reset_minutes=None):
    return {"id": rid, "model": model, "families": eligible_families(model), "access": access,
            "available": available, "cash": cash, "allocation": allocation,
            "reset_minutes": reset_minutes}


# Free routes used in TD 1 (cash 0, allocation 0) and paid routes of the same models.
RESOURCES = [
    resource("groq:openai/gpt-oss-20b", "gpt-oss-20b", "free", 0.0),
    resource("groq:openai/gpt-oss-120b", "gpt-oss-120b", "free", 0.0),
    resource("groq:qwen/qwen3.8-27b", "qwen3.8-27b", "free", 0.0),
    resource("openrouter:cohere/north-mini-code:free", "north-mini-code", "free", 0.0),
    resource("openrouter:dots-studio/dots-3-note-preview:free", "dots-3-note-preview", "free", 0.0),
    # 641 x 0.018 + 243 x 0.09 per million tokens
    resource("openrouter:openai/gpt-oss-20b", "gpt-oss-20b", "tokens", 0.000033),
    # 641 x 0.15 + 234 x 0.60 per million tokens
    resource("openrouter:openai/gpt-oss-120b", "gpt-oss-120b", "tokens", 0.000237),
]

# Paid-route price used to break ties between free routes (cheapest fallback first).
TIE_BREAK = {"gpt-oss-20b": 0, "gpt-oss-120b": 1, "qwen3.8-27b": 2,
             "north-mini-code": 3, "dots-3-note-preview": 4}

AGE_FAMILIES = {"F2", "F2b", "F1+F2", "F2+F3", "F1+F2+F3", "F1+F2b"}


def checks_for(request, chosen_model):
    """Checking required by the rule, from the family and the cost of an error."""
    family, use = request["family"], request["use"]
    if use == "dashboard":
        # 'none' only if the chosen model is 100 % on the family (always true
        # here, since only eligible resources are chosen).
        return "none (internal dashboard, %s %s on %s)" % (chosen_model, TD1[chosen_model][family], family)
    if use == "customer":
        if family in AGE_FAMILIES:
            return "deterministic check against the reference SQL template (refs/) before display"
        return "2-of-3 quorum (gpt-oss-20b, gpt-oss-120b, qwen3.8-27b: 100 %% on %s)" % family
    # payout
    if family in AGE_FAMILIES:
        return "deterministic reference query + human review before payment"
    return "3-of-5 quorum + deterministic reference query before payment"


def reason(prefix, r, family):
    cells = ", ".join(FAMILIES[family])
    return "%s; %s is %s on %s in TD 1 (%s)" % (prefix, r["model"], TD1[r["model"]][family], family, cells)


def choose(request, resources):
    """Same priority order as the supplied policy, eligibility by TD 1 family."""
    family = request["family"]
    eligible = [r for r in resources if family in r["families"]]
    included = [r for r in eligible if r["available"] and r["cash"] == 0]
    if included:
        chosen = min(included, key=lambda r: (r["allocation"], TIE_BREAK[r["model"]], r["id"]))
        return {"action": "run", "resource": chosen["id"], "cash": 0,
                "checks": checks_for(request, chosen["model"]),
                "reason": reason("eligible free capacity", chosen, family)}
    waiting = [r for r in eligible if not r["available"] and r["cash"] == 0
               and r["reset_minutes"] is not None
               and 0 < r["reset_minutes"] <= request["deadline_minutes"]]
    if waiting and request["can_wait"]:
        chosen = min(waiting, key=lambda r: r["reset_minutes"])
        return {"action": "defer", "resource": chosen["id"], "cash": 0,
                "checks": checks_for(request, chosen["model"]),
                "reason": reason("free quota exhausted, refill before deadline; recheck at wake-up",
                                 chosen, family),
                "wake_in_minutes": chosen["reset_minutes"]}
    paid = [r for r in eligible if r["available"] and r["cash"] <= request["budget"]]
    if paid:
        chosen = min(paid, key=lambda r: (r["cash"], r["allocation"], r["id"]))
        return {"action": "run", "resource": chosen["id"], "cash": chosen["cash"],
                "checks": checks_for(request, chosen["model"]),
                "reason": reason("paid route of a TD 1-eligible model, within budget "
                                 "(assumes the paid route serves the same weights)", chosen, family)}
    return {"action": "abstain", "resource": None, "cash": 0,
            "checks": "none: no value is produced",
            "reason": "no model 100 %% correct on %s in TD 1 is available within deadline and budget "
                      "(cells %s)" % (family, ", ".join(FAMILIES.get(family, [])) or "none measured")}


def scenarios():
    base = {"family": "F1", "use": "dashboard", "can_wait": True,
            "deadline_minutes": 120, "budget": 0.001}

    def groq_429(minutes):
        """Groq free plan rate-limited (as for qwen on C18 in TD 1)."""
        return [dict(r, available=False, reset_minutes=minutes) if r["id"].startswith("groq:") else dict(r)
                for r in RESOURCES]

    return [
        ("simple", base, RESOURCES),
        ("complex", {**base, "family": "F2"}, RESOURCES),
        ("deferrable", {**base, "family": "F2"}, groq_429(60)),
        ("urgent", {**base, "family": "F2", "can_wait": False, "deadline_minutes": 5}, groq_429(60)),
        ("budget exhausted", {**base, "family": "F2", "can_wait": False, "budget": 0}, groq_429(60)),
        ("high impact", {**base, "family": "F1+F2+F3", "use": "payout"}, RESOURCES),
        ("unknown capability", {**base, "family": "F4"}, RESOURCES),
        ("customer period", {**base, "use": "customer"}, RESOURCES),
        ("combined age at order, groq down", {**base, "family": "F1+F2b", "use": "customer",
                                              "can_wait": False}, groq_429(60)),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", help="show only the named scenario")
    args = parser.parse_args()
    found = False
    for name, request, resources in scenarios():
        if args.scenario and name != args.scenario:
            continue
        found = True
        print(json.dumps({"scenario": name, "nature": "simulation", "request": request,
                          "result": choose(request, resources)}))
    if not found:
        parser.error("unknown scenario")


if __name__ == "__main__":
    main()
