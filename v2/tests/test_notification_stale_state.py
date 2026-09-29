#!/usr/bin/env python3
import subprocess
CMD=["python3","v2/gates/verify_notification_stale_state.py"]
def c(name,args,need):
 p=subprocess.run(CMD+args,text=True,capture_output=True);o=p.stdout+p.stderr
 if p.returncode or any(x not in o for x in need):raise SystemExit(name+" failed:\n"+o)
 print("PASS notification case:",name)
 for line in o.splitlines():
  if line.startswith(("NOTIFICATION STALE","RESYNC_REQUIRED","RESOLVED:","USER_DECISION_REQUIRED:","CURRENT:")):print("  "+line)
same="a"*40;old="b"*40
c("current-registry-coverage-consistent",["--notification-head",same,"--current-head",same,"--notification-run","100","--current-run","100","--resolved","false"],["CURRENT:"])
c("stale-rejected-and-resync",["--notification-head",old,"--current-head",same,"--notification-run","99","--current-run","100","--resolved","false"],["NOTIFICATION STALE","RESYNC_REQUIRED","USER_DECISION_REQUIRED"])
c("stale-already-resolved-no-reprompt",["--notification-head",old,"--current-head",same,"--notification-run","99","--current-run","100","--resolved","true"],["NOTIFICATION STALE","RESYNC_REQUIRED","RESOLVED: original requested action is already satisfied; user re-prompt forbidden"])
c("stale-unresolved-reprompt-current-state",["--notification-head",old,"--current-head",same,"--notification-run","99","--current-run","100","--resolved","false"],["RESYNC_REQUIRED: current_head="+same+" current_run=100","USER_DECISION_REQUIRED"])
print("PASS notification stale-state destructive/behavior cases")
