import json, sys
S = json.load(open("build/ui-audit/tool_schemas.json"))
H = json.load(open("docs/ui/hints_loads.json"))
def names(sch, pre=""):
    defs, out = sch.get("$defs", {}), {}
    for f, s in sch.get("properties", {}).items():
        opts = [s] + [o for k in ("anyOf", "oneOf") for o in s.get(k, [])]
        u = next((defs[o["$ref"].split("/")[-1]] for o in opts if "$ref" in o), s)
        out[pre + f] = u
        if u is not s: out.update(names({**u, "$defs": defs}, pre + f + "."))
        it = (u.get("items") or {})
        ir = defs.get(it.get("$ref", "").split("/")[-1], it)
        for c in ir.get("properties", {}): out[pre + f + "." + c] = {}
    return out
bad = []
for tool, h in H.items():
    if tool.startswith("_"): continue
    if tool not in S: bad.append(f"{tool}: unknown tool"); continue
    ins, outs = names(S[tool]["input"]), names(S[tool]["output"])
    rows = {k: v for k, v in outs.items()}
    for k in h.get("input_groups", {}):
        if k not in ins: bad.append(f"{tool}.input_groups.{k}")
    for sec in ("label_fixes", "symbols", "units_missing"):
        for k in h.get(sec, {}):
            if k not in ins and k not in outs: bad.append(f"{tool}.{sec}.{k}")
    for k in h.get("highlight", []):
        if k not in outs: bad.append(f"{tool}.highlight.{k}")
    for rowf, c in h.get("chart", {}).items():
        if rowf not in outs: bad.append(f"{tool}.chart.{rowf}")
        for col in [c["x"]] + c["y"]:
            if rowf + "." + col not in outs: bad.append(f"{tool}.chart.{rowf}.{col}")
print("OK" if not bad else "BROKEN REFS:\n" + "\n".join(bad))
sys.exit(1 if bad else 0)
