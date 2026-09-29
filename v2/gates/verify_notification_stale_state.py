#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]; P=json.loads((R/"v2/gates/notification_stale_state.json").read_text())
def classify(nh,ch,nr,cr,resolved):
 if nh==ch and nr==cr:return "CURRENT"
 if resolved:return "RESOLVED"
 return "USER_DECISION_REQUIRED"
def main():
 a=argparse.ArgumentParser();a.add_argument("--notification-head",required=True);a.add_argument("--current-head",required=True);a.add_argument("--notification-run",required=True);a.add_argument("--current-run",required=True);a.add_argument("--resolved",choices=["true","false"],required=True);x=a.parse_args()
 stale=x.notification_head!=x.current_head or x.notification_run!=x.current_run
 if stale: print("NOTIFICATION STALE: old Commit/Run rejected as current authority");print("RESYNC_REQUIRED: current_head="+x.current_head+" current_run="+x.current_run)
 state=classify(x.notification_head,x.current_head,x.notification_run,x.current_run,x.resolved=="true")
 if state=="RESOLVED":print("RESOLVED: original requested action is already satisfied; user re-prompt forbidden")
 elif state=="USER_DECISION_REQUIRED":print("USER_DECISION_REQUIRED: present current HEAD/Run and ask only the still-unresolved decision")
 else:print("CURRENT: notification matches repository current state")
if __name__=="__main__":main()
