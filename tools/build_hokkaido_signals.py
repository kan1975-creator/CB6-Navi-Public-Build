#!/usr/bin/env python3
"""OFFLINE CANDIDATE ONLY. Generate an UNSIGNED SQLite for subsequent owner review.

No keys, GitHub interactions, network requests or automatic signing.
Requires pyosmium (osmium), provisioned separately after further authorization.
Do not execute before the separate database-generation approval.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import tempfile
from collections import defaultdict, deque

FIXED_PBF_SHA256 = '2e4ac16f5b269624a36e3087c10466e080a71185de3440c488e188ef55320726'
FIXED_PBF_SIZE = 189578209
WAY_NS = 1 << 62
REL_NS = (1 << 62) | (1 << 61)
SCHEMA = 1
# Proof must come from exactly shared OSM road graph nodes, never lat/lon proximity alone.
MAX_GRAPH_DIST_M = 30.0
MAX_GROUP_SPREAD_M = 80.0
# Roads with verifiable car-accessible geometry; no footways, paths, cycleways,
# steps, construction or inferred crossings may form a certified group.
CERTIFIED_ROADS = frozenset({
    'motorway', 'trunk', 'primary', 'secondary', 'tertiary',
    'unclassified', 'residential', 'living_street',
})


def certified_road(w):
    return (w.tags.get('highway') in CERTIFIED_ROADS
            and w.tags.get('area') != 'yes'
            and w.tags.get('bridge') not in ('yes', 'true', '1')
            and w.tags.get('tunnel') not in ('yes', 'true', '1')
            and w.tags.get('layer') in (None, '', '0')
            and w.tags.get('access') not in ('no', 'private'))


def sha256_file(path):
    h = hashlib.sha256()
    with path.open('rb') as src:
        while True:
            block = src.read(1024 * 1024)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def distance_m(a, b):
    dy = (a[0] - b[0]) * 111195.0
    dx = (a[1] - b[1]) * 111195.0 * math.cos(math.radians((a[0]+b[0])/2))
    return math.hypot(dy, dx)


def derive_confirmed_groups(signals, road_edges, road_coords, node_road_ways):
    """Only shared-node, multi-way road junctions establish 200m identity.

    The exact OSM node must have >=3 graph neighbors AND >=2 distinct
    permitted road way IDs. Geometric near-misses, paths, elevated links,
    parallel roads, uncertain junctions and incomplete source evidence fail open.
    """
    adjacency = defaultdict(set)
    for a, b in road_edges:
        if a != b:
            adjacency[a].add(b)
            adjacency[b].add(a)
    junctions = {n for n, near in adjacency.items()
                 if len(near) >= 3 and len(node_road_ways.get(n, ())) >= 2}
    candidates = defaultdict(list)
    for raw_id, pos in signals.items():
        if raw_id not in adjacency:
            continue
        q = deque([(raw_id, 0.0)])
        reached = {raw_id: 0.0}
        found = set()
        while q:
            node, walked = q.popleft()
            if node in junctions:
                found.add(node)
            for nxt in adjacency[node]:
                if nxt not in road_coords or node not in road_coords:
                    continue
                new_dist = walked + distance_m(road_coords[node], road_coords[nxt])
                if new_dist > MAX_GRAPH_DIST_M:
                    continue
                if new_dist + 1e-5 < reached.get(nxt, 1e100):
                    reached[nxt] = new_dist
                    q.append((nxt, new_dist))
        if len(found) == 1:
            centre = next(iter(found))
            candidates[centre].append(raw_id)
    groups = {}
    for junction_id, members in candidates.items():
        if len(members) < 2:
            continue
        if any(distance_m(signals[a], signals[b]) > MAX_GROUP_SPREAD_M
               for i, a in enumerate(members) for b in members[i+1:]):
            continue
        for member in members:
            groups[member] = (junction_id, road_coords[junction_id])
    return groups


def make_database(pbf, dest, source_sha=FIXED_PBF_SHA256,
                  source_bytes=FIXED_PBF_SIZE, source_date='2026-10-12',
                  expected_nodes=21466, expected_ways=7419, expected_roads=590216):
    try:
        import osmium
    except ImportError as exc:
        raise SystemExit('Missing pyosmium; STOP (do not silently switch parsers)') from exc
    if pbf.stat().st_size != source_bytes or sha256_file(pbf) != source_sha:
        raise SystemExit('PBF identity differs from explicitly approved source; STOP')
    if len(source_sha)!=64 or not all(c in '0123456789abcdef' for c in source_sha):
        raise SystemExit('Invalid approved PBF SHA-256')
    if len(source_date)!=10 or source_date[4]!='-' or source_date[7]!='-':
        raise SystemExit('Invalid source date')

    node_signals = {}
    class SignalNodes(osmium.SimpleHandler):
        def node(self, n):
            if n.tags.get('highway') == 'traffic_signals' or n.tags.get('crossing') == 'traffic_signals':
                if n.location.valid():
                    node_signals[int(n.id)] = (float(n.location.lat), float(n.location.lon))
    SignalNodes().apply_file(str(pbf))

    signal_ways = {}
    road_edges = set()
    road_coords = {}
    node_road_ways = defaultdict(set)
    seed_nodes = set()
    road_way_count = 0
    class Ways(osmium.SimpleHandler):
        def way(self, w):
            nonlocal road_way_count
            is_signal = w.tags.get('crossing') == 'traffic_signals'
            is_road = 'highway' in w.tags
            if not (is_road or is_signal):
                return
            refs = [int(n.ref) for n in w.nodes]
            if is_signal:
                coords = [(float(n.location.lat), float(n.location.lon))
                          for n in w.nodes if n.location.valid()]
                if len(coords) != len(refs) or not coords:
                    raise ValueError('Signal way geometry incomplete: '+str(w.id))
                # OSM/Overpass 'out center' is the way bounding-box centre.
                lat = (min(v[0] for v in coords)+max(v[0] for v in coords))/2.0
                lon = (min(v[1] for v in coords)+max(v[1] for v in coords))/2.0
                signal_ways[int(w.id)] = (lat, lon)
            if is_road:
                road_way_count += 1  # Count ALL highway-tagged ways for source audit.
                if certified_road(w) and any(n in node_signals for n in refs):
                    seed_nodes.update(refs)
    Ways().apply_file(str(pbf), locations=True)

    # Only the first-hop roads touching a verified signal roadway and roads
    # attached to THEIR OSM graph nodes participate. Do not infer adjacency by
    # spatial closeness or count footpaths as vehicular junction branches.
    class TopologyWays(osmium.SimpleHandler):
        def way(self, w):
            if not certified_road(w):
                return
            refs = [int(n.ref) for n in w.nodes]
            if len(refs) < 2 or not any(n in seed_nodes for n in refs):
                return
            coords = [(float(n.location.lat), float(n.location.lon))
                      for n in w.nodes if n.location.valid()]
            if len(coords) != len(refs):
                return  # Missing geometry is unknown, not confirmation.
            for n, pos in zip(refs, coords):
                road_coords[n] = pos
                node_road_ways[n].add(int(w.id))
            for a, b in zip(refs, refs[1:]):
                if a != b:
                    road_edges.add((min(a,b), max(a,b)))
    TopologyWays().apply_file(str(pbf), locations=True)
    relation_signals=[]
    class SignalRelations(osmium.SimpleHandler):
        def relation(self, rel):
            if rel.tags.get('type') == 'traffic_signals_set':
                relation_signals.append(int(rel.id))
    SignalRelations().apply_file(str(pbf))
    # Initial approved source contains zero signal-set relations. Future formats
    # must not be silently dropped; require a separate scoped review instead.
    if relation_signals:
        raise SystemExit('STOP: signal-set relations need explicit topology support')
    if (len(node_signals)!=expected_nodes or len(signal_ways)!=expected_ways
            or road_way_count!=expected_roads):
        raise SystemExit('OSM tag counts differ from approved fixed source; STOP')
    groups = derive_confirmed_groups(node_signals, road_edges, road_coords, node_road_ways)

    if dest.exists():
        raise SystemExit('Destination exists: refuse overwrite')
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix='.cb6-candidate-', suffix='.sqlite', dir=str(dest.parent))
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        db = sqlite3.connect(str(tmp))
        db.executescript('''
            PRAGMA page_size=4096;
            CREATE TABLE metadata(k TEXT PRIMARY KEY, v TEXT NOT NULL);
            CREATE TABLE signals(
              id INTEGER PRIMARY KEY, osm_type TEXT NOT NULL, osm_id INTEGER NOT NULL,
              lat REAL NOT NULL, lon REAL NOT NULL,
              group_id INTEGER NOT NULL DEFAULT 0,
              center_lat REAL NOT NULL DEFAULT 0, center_lon REAL NOT NULL DEFAULT 0);
            CREATE VIRTUAL TABLE signal_index USING rtree(
              id, min_lat, max_lat, min_lon, max_lon);
        ''')
        with db:
            for raw_id, (lat, lon) in sorted(node_signals.items()):
                group_id, center = groups.get(raw_id, (0, (0.0,0.0)))
                db.execute('INSERT INTO signals VALUES(?,?,?,?,?,?,?,?)',
                           (raw_id, 'node', raw_id, lat, lon, group_id, center[0], center[1]))
                db.execute('INSERT INTO signal_index VALUES(?,?,?,?,?)', (raw_id,lat,lat,lon,lon))
            for raw_id, (lat, lon) in sorted(signal_ways.items()):
                uid = WAY_NS | raw_id
                db.execute('INSERT INTO signals VALUES(?,?,?,?,?,?,?,?)',
                           (uid,'way',raw_id,lat,lon,0,0,0))
                db.execute('INSERT INTO signal_index VALUES(?,?,?,?,?)', (uid,lat,lat,lon,lon))
            meta = {
                'schema': str(SCHEMA), 'region': 'hokkaido', 'osm_date': source_date,
                'pbf_sha256': source_sha, 'odbl': 'https://www.openstreetmap.org/copyright',
                'count_node': str(len(node_signals)), 'count_way': str(len(signal_ways)),
                'count_relation': '0', 'count_highway_ways': str(road_way_count),
                'confirmed_member_count': str(len(groups))}
            db.executemany('INSERT INTO metadata VALUES (?,?)', sorted(meta.items()))
        integrity = db.execute('PRAGMA integrity_check').fetchone()[0]
        db.close()
        if integrity != 'ok':
            raise ValueError('SQLite integrity failure')
        # Atomic candidate creation; never signs or modifies repository / device.
        os.replace(tmp, dest)
        return meta
    finally:
        if tmp.exists():
            tmp.unlink()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('approved_pbf', type=Path)
    p.add_argument('unsigned_candidate_sqlite', type=Path)
    p.add_argument('--unsigned-output-dir', type=Path, default=None,
                   help='Optional staging directory for unsigned manifest and ODbL attribution')
    p.add_argument('--future-sha256', default=None)
    p.add_argument('--future-bytes', type=int, default=None)
    p.add_argument('--future-date', default=None)
    p.add_argument('--future-node-count', type=int, default=None)
    p.add_argument('--future-way-count', type=int, default=None)
    p.add_argument('--future-highway-way-count', type=int, default=None)
    p.add_argument('--future-geofabrik-url', default=None)
    args = p.parse_args()
    future = (args.future_sha256,args.future_bytes,args.future_date,args.future_node_count,
              args.future_way_count,args.future_highway_way_count,args.future_geofabrik_url)
    if any(v is not None for v in future) and not all(v is not None for v in future):
        raise SystemExit('STOP: future source requires all seven owner-approved fields')
    if future[-1] is not None and not future[-1].startswith(
           'https://download.geofabrik.de/asia/japan/hokkaido-'):
        raise SystemExit('STOP: not a Geofabrik Hokkaido date-version URL')
    source_sha=args.future_sha256 or FIXED_PBF_SHA256
    source_bytes=args.future_bytes or FIXED_PBF_SIZE
    source_date=args.future_date or '2026-10-12'
    node_count=args.future_node_count if args.future_node_count is not None else 21466
    way_count=args.future_way_count if args.future_way_count is not None else 7419
    road_count=args.future_highway_way_count if args.future_highway_way_count is not None else 590216
    meta = make_database(args.approved_pbf, args.unsigned_candidate_sqlite,
              source_sha,source_bytes,source_date,node_count,way_count,road_count)
    if args.unsigned_output_dir:
        out=args.unsigned_output_dir
        out.mkdir(parents=True,exist_ok=True)
        manifest=out/'manifest.json'
        attribution=out/'ATTRIBUTION.txt'
        if manifest.exists() or attribution.exists():
            raise SystemExit('STOP: unsigned output already exists')
        attr=b'Contains OpenStreetMap contributors data, licensed under ODbL 1.0.\nhttps://www.openstreetmap.org/copyright\n'
        manifest_data={
          'schema':SCHEMA, 'region':'hokkaido', 'version':int(source_date.replace('-','')),
          'pbf_sha256':source_sha,
          'sqlite_sha256':sha256_file(args.unsigned_candidate_sqlite),
          'sqlite_bytes':args.unsigned_candidate_sqlite.stat().st_size,
          'signal_count':int(meta['count_node'])+int(meta['count_way'])+int(meta['count_relation']),
          'attribution_sha256':hashlib.sha256(attr).hexdigest(),
          'source':'OpenStreetMap contributors (ODbL 1.0)',
          'source_url':args.future_geofabrik_url or 'https://download.geofabrik.de/asia/japan/hokkaido-261012.osm.pbf'}
        # manifest.sig must later be generated with owner-only key; NEVER auto-sign.
        attribution.write_bytes(attr)
        manifest.write_bytes((json.dumps(manifest_data,sort_keys=True,separators=(',',':'))+'\n').encode('utf-8'))
    print(json.dumps(meta, sort_keys=True))
    print('UNSIGNED CANDIDATE ONLY; NO RELEASE OR SIGNATURE')

if __name__ == '__main__':
    main()
