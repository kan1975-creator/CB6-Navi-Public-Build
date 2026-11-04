#!/usr/bin/env python3
"""Count Hokkaido OSM signals using the unchanged generator's tag rules."""
import argparse
import json
from pathlib import Path
import osmium

class SignalNodes(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.ids = set()
    def node(self, n):
        if (n.tags.get('highway') == 'traffic_signals' or n.tags.get('crossing') == 'traffic_signals') and n.location.valid():
            self.ids.add(int(n.id))

class Ways(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.signal_ids = set()
        self.road_count = 0
    def way(self, w):
        if w.tags.get('crossing') == 'traffic_signals':
            refs = [int(n.ref) for n in w.nodes]
            coords = [(float(n.location.lat), float(n.location.lon)) for n in w.nodes if n.location.valid()]
            if len(coords) != len(refs) or not coords:
                raise ValueError('Signal way geometry incomplete: ' + str(w.id))
            self.signal_ids.add(int(w.id))
        if 'highway' in w.tags:
            self.road_count += 1

class Relations(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.found = []
    def relation(self, r):
        if r.tags.get('type') == 'traffic_signals_set':
            self.found.append(int(r.id))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('pbf', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('STOP: output exists')
    n = SignalNodes()
    n.apply_file(str(args.pbf))
    w = Ways()
    w.apply_file(str(args.pbf), locations=True)
    r = Relations()
    r.apply_file(str(args.pbf))
    if r.found:
        raise SystemExit('STOP: signal-set relations require explicit support')
    data = {'signal_nodes':len(n.ids),'signal_ways':len(w.signal_ids),'highway_ways':w.road_count,'signal_set_relations':0}
    args.output.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(data))

if __name__ == '__main__':
    main()
