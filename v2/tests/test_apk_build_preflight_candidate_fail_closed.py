#!/usr/bin/env python3
import copy, json, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
d=json.loads((ROOT/"v2/gates/apk_build_preflight_candidate.json").read_text())
def valid(x):
    r=x.get("requirements",{})
    return x.get("status")=="PROPOSED" and x.get("fail_closed") is True and x.get("placement")=="immediately_before_gradle_apk_build" and all(v is True for v in r.values())
assert valid(d)
for key in d["requirements"]:
    x=copy.deepcopy(d); x["requirements"][key]=False; assert not valid(x), key
x=copy.deepcopy(d); x["fail_closed"]=False; assert not valid(x)
x=copy.deepcopy(d); x["status"]="ACTIVE"; assert not valid(x)
print("APK Build Preflight destructive candidate tests: PASS")
