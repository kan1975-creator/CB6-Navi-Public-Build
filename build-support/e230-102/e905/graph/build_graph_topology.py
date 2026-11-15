#!/usr/bin/env python3
"""Build offline junction membership from the OSM motor-road graph.

Branches are barriers, never distance-clustered. A wide intersection can join
branch nodes only around a compact directed carriageway cycle with the same
two named/ref road corridors at every corner. Overlapping cycles are rejected.
Unresolved signals remain independent. No on-device graph traversal is needed.
"""
import collections, csv, json, math, pathlib, re, sqlite3, sys

MOTOR = {'motorway','trunk','primary','secondary','tertiary','unclassified',
         'residential','living_street','service','motorway_link','trunk_link',
         'primary_link','secondary_link','tertiary_link'}
def decode(s):
    return re.sub(r'%([0-9a-fA-F]+)%', lambda m: chr(int(m[1],16)), s)
def parse(line):
    fields=line.rstrip().split(' ')
    d={x[0]:x[1:] for x in fields[1:] if x}
    tags=dict((decode(k),decode(v)) for t in d.get('T','').split(',') if '=' in t for k,v in [t.split('=',1)])
    return int(fields[0][1:]), d, tags
def distance(a,b):
    p,q=math.radians(a[0]),math.radians(b[0])
    x=math.sin((q-p)/2)**2+math.cos(p)*math.cos(q)*math.sin(math.radians(b[1]-a[1])/2)**2
    return 12742000*math.asin(min(1,math.sqrt(x)))

def build(roads, source_db, output):
    coords={}; graph=collections.defaultdict(set); corridors=collections.defaultdict(set)
    directed=set()
    with open(roads) as f:
        for line in f:
            if line.startswith('n'):
                # Coordinates only: avoid decoding millions of unrelated tags.
                fields=line.rstrip().split(' '); d={x[0]:x[1:] for x in fields[1:] if x}
                if d.get('x') and d.get('y'): coords[int(fields[0][1:])]=(float(d['y']),float(d['x']))
            elif line.startswith('w'):
                wid,d,t=parse(line)
                if t.get('highway') not in MOTOR or any(t.get(k) in {'no','private'} for k in ('motor_vehicle','motorcar','vehicle','access')):continue
                ns=[int(n[1:]) for n in d.get('N','').split(',') if n.startswith('n')]
                key=('ref:'+t['ref']) if t.get('ref') else ('name:'+t['name']) if t.get('name') else ''
                for n in ns:
                    if key:corridors[n].add(key)
                for a,b in zip(ns,ns[1:]):
                    if a==b:continue
                    graph[a].add(b);graph[b].add(a)
                    if t.get('oneway') in ('yes','1','true'):directed.add((a,b))
                    elif t.get('oneway')=='-1':directed.add((b,a))
    print('motor graph loaded',len(graph),flush=True)
    with sqlite3.connect('file:'+str(pathlib.Path(source_db).resolve())+'?mode=ro',uri=True) as db:
        signals={int(i):(float(y),float(x)) for i,x,y in db.execute("SELECT osm_node_id,longitude,latitude FROM signal_classification WHERE classification='VEHICLE_CONFIRMED'")}
    coords.update(signals)
    branches={n for n,adj in graph.items() if len(adj)>=3}
    # Contract degree-two shape nodes to the next branch, bounded to the
    # intersection interior. Edges between intersections cannot trigger a union.
    links=collections.defaultdict(dict)
    relevant=set()
    def walk(start,nxt,limit=100):
        prev=start; node=nxt; length=0.; forward=True; backward=True; path=[start]
        for _ in range(64):
            if node not in coords or prev not in coords:return None
            length+=distance(coords[prev],coords[node])
            if length>limit or node in path:return None
            forward=forward and (prev,node) in directed
            backward=backward and (node,prev) in directed
            path.append(node)
            if node in branches:return node,length,forward,backward,path
            if len(graph[node])!=2:return None
            next_node=next(x for x in graph[node] if x!=prev)
            prev,node=node,next_node
        return None
    for sid in signals:
        if sid in branches:relevant.add(sid)
        for nxt in graph.get(sid,()):
            w=walk(sid,nxt)
            if w:relevant.add(w[0])
    # Two rings are enough for a four-corner divided-road junction.
    frontier=set(relevant)
    for _ in range(2):
        following=set()
        for n in frontier:
            for nxt in graph[n]:
                w=walk(n,nxt)
                if w:
                    end,length,fw,bw,path=w
                    if fw or bw:links[n][end]=(length,fw,bw,path)
                    following.add(end)
        frontier=following-set(links)
    cycles=set()
    for a in relevant:
        keys=corridors[a]
        if len(keys)!=2:continue
        for b in links[a]:
            if corridors[b]!=keys:continue
            for c in links[b]:
                if c==a or corridors[c]!=keys:continue
                for d in links[c]:
                    if d in (a,b) or a not in links[d] or corridors[d]!=keys:continue
                    ring=(a,b,c,d)
                    # Require one directed cycle, not four nearby branches.
                    if not all(links[x][y][1] for x,y in zip(ring,ring[1:]+ring[:1])):continue
                    if any(distance(coords[x],coords[y])>100 for x in ring for y in ring):continue
                    if sum(links[x][y][0] for x,y in zip(ring,ring[1:]+ring[:1]))>300:continue
                    if any(len(graph[x])<3 for x in ring):continue
                    cycles.add(frozenset(ring))
    appearances=collections.Counter(n for ring in cycles for n in ring)
    wide=[ring for ring in cycles if all(appearances[n]==1 for n in ring)]
    junctions={n:n for n in branches}
    for ring in wide:
        for n in ring:junctions[n]=min(ring)
    # E981's first-junction rule: stop at each branching barrier. Different
    # first-junction identities make a signal ambiguous; never pick nearest.
    assigned={}; members=collections.defaultdict(list)
    for sid in signals:
        found=set()
        if sid in junctions:found.add(junctions[sid])
        else:
            for nxt in graph.get(sid,()):
                w=walk(sid,nxt)
                if w:found.add(junctions[w[0]])
        if len(found)==1:
            group=next(iter(found));assigned[sid]=group;members[group].append(sid)
    representatives={g:min(ids,key=lambda i:(distance(signals[i],coords[g]),i)) for g,ids in members.items()}
    output=pathlib.Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['member_id','center_id','member_lat','member_lon','center_lat','center_lon'])
        for sid in sorted(signals):
            rep=representatives[assigned[sid]] if sid in assigned else sid
            writer.writerow([sid,rep,*signals[sid],*signals[rep]])
    print(json.dumps({'vehicle_nodes':len(signals),'assigned':len(assigned),'junctions':len(members),'wide_junctions':len(wide),'collapsed':sum(len(v)-1 for v in members.values()),'independent_unresolved':len(signals)-len(assigned)}),flush=True)

if __name__=='__main__':build(*sys.argv[1:])
