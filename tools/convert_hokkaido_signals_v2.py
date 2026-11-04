#!/usr/bin/env python3
"""CB6 V2 candidate converter. No OSM extraction, hashing, signing, or network I/O.

Conservative policy: preserve R43 evidence; do not promote it to topology.
Input remains read-only; output is created only after successful validation.
"""
import argparse
import math
import os
from pathlib import Path
import sqlite3
import tempfile

MAX_ROWS = 250000
MAX_NODE_ID = (1 << 61) - 1
WAY_NS = 1 << 62

def require(ok, message):
    if not ok:
        raise ValueError(message)

def valid_coord(lat, lon):
    return (math.isfinite(lat) and math.isfinite(lon)
            and -90 <= lat <= 90 and -180 <= lon <= 180)

def check_columns(db, table, required):
    names = {r[1] for r in db.execute(f"PRAGMA table_info({table})")}
    require(set(required) <= names, f"Missing columns in {table}")

def convert(source: Path, output: Path):
    require(source.is_file() and not source.is_symlink(), "Input must be a regular file")
    require(not output.exists() and not output.is_symlink(), "Output already exists")
    require(source.resolve() != output.resolve(), "Input/output collision")
    require(output.parent.is_dir(), "Output parent must exist")
    uri = source.resolve().as_uri() + "?mode=ro&immutable=1"
    with sqlite3.connect(uri, uri=True) as src:
        require(src.execute("PRAGMA integrity_check").fetchone()[0] == "ok",
                "Input integrity_check failed")
        check_columns(src, "signals", ("id", "osm_type", "osm_id", "lat", "lon",
                                        "group_id", "center_lat", "center_lon"))
        check_columns(src, "metadata", ("k", "v"))
        metadata_rows = list(src.execute("SELECT k,v FROM metadata"))
        require(all(type(k) is str and type(v) is str for k, v in metadata_rows),
                "Invalid metadata types")
        metadata = dict(metadata_rows)
        require(len(metadata) == len(metadata_rows), "Duplicate metadata keys")
        require(metadata.get("region") == "hokkaido", "Wrong region")
        version = metadata.get("osm_date")
        require(isinstance(version, str) and len(version) == 10
                and version[4] == "-" and version[7] == "-"
                and version.replace("-", "").isdigit(), "Invalid osm_date")
        require(metadata.get("pbf_sha256") is not None
                and len(metadata["pbf_sha256"]) == 64
                and all(c in "0123456789abcdef" for c in metadata["pbf_sha256"]),
                "Missing or malformed source PBF digest metadata")
        # This checks metadata shape, NOT PBF authenticity.
        rows = list(src.execute(
            "SELECT id,osm_type,osm_id,lat,lon,group_id,center_lat,center_lon "
            "FROM signals ORDER BY id"))
        require(0 < len(rows) <= MAX_ROWS, "Invalid signal count")
        seen = set()
        signals, evidence = [], []
        for sid, kind, osm_id, lat, lon, group, clat, clon in rows:
            require(type(sid) is int and type(osm_id) is int
                    and 0 < osm_id <= MAX_NODE_ID
                    and kind in ("node", "way"), "Invalid source ID")
            expected_id = osm_id if kind == "node" else WAY_NS | osm_id
            require(sid == expected_id and sid not in seen, "Invalid/duplicate ID")
            seen.add(sid)
            require(type(lat) is float and type(lon) is float
                    and valid_coord(lat, lon), "Invalid coordinate")
            signals.append((sid, lat, lon, "osm", kind, osm_id))
            require(type(group) is int, "Invalid group type")
            if group:
                require(group > 0 and type(clat) is float and type(clon) is float
                        and valid_coord(clat, clon), "Invalid R43 evidence")
                evidence.append((sid, group, clat, clon))
            else:
                require(clat == 0 and clon == 0, "Unexpected ungrouped center")
        if "count_node" in metadata:
            require(int(metadata["count_node"]) ==
                    sum(s[4] == "node" for s in signals), "Node count mismatch")
        if "count_way" in metadata:
            require(int(metadata["count_way"]) ==
                    sum(s[4] == "way" for s in signals), "Way count mismatch")
        if "confirmed_member_count" in metadata:
            require(int(metadata["confirmed_member_count"]) == len(evidence),
                    "Evidence count mismatch")

        fd, temp = tempfile.mkstemp(prefix=".cb6-v2-", suffix=".sqlite",
                                    dir=str(output.parent))
        os.close(fd)
        try:
            with sqlite3.connect(temp) as dst:
                dst.executescript("""
                    PRAGMA user_version=2;
                    CREATE TABLE package_info (
                      schema_version INTEGER NOT NULL,
                      dataset_version TEXT NOT NULL,
                      source TEXT NOT NULL);
                    CREATE TABLE signals (
                      id INTEGER PRIMARY KEY,
                      latitude REAL NOT NULL,
                      longitude REAL NOT NULL,
                      source_type TEXT NOT NULL,
                      osm_type TEXT NOT NULL,
                      osm_id INTEGER NOT NULL);
                    CREATE TABLE r43_group_evidence (
                      member_id INTEGER PRIMARY KEY,
                      original_group_id INTEGER NOT NULL,
                      original_center_lat REAL NOT NULL,
                      original_center_lon REAL NOT NULL);
                    CREATE TABLE topology (
                      member_id INTEGER PRIMARY KEY,
                      center_id INTEGER NOT NULL);
                """)
                dst.execute("INSERT INTO package_info VALUES(2,?,?)",
                            (version, "osm"))
                dst.executemany("INSERT INTO signals VALUES(?,?,?,?,?,?)", signals)
                dst.executemany("INSERT INTO r43_group_evidence VALUES(?,?,?,?)",
                                evidence)
                # Intentionally empty: old R43 center coordinates do not prove
                # a current signal ID or a direct <=15m non-chained topology.
                require(dst.execute("PRAGMA integrity_check").fetchone()[0] == "ok",
                        "Output integrity_check failed")
                require(dst.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
                        == len(signals), "Output count mismatch")
                require(dst.execute("SELECT COUNT(*) FROM r43_group_evidence").fetchone()[0]
                        == len(evidence), "Evidence count mismatch")
                dst.commit()
            # Sync the closed SQLite file before exposing a new hard link.
            with open(temp, "rb") as ready:
                os.fsync(ready.fileno())
            # Exclusive publication: never overwrite an existing destination.
            os.link(temp, output)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
    return len(signals), len(evidence)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    count, evidence = convert(args.source, args.output)
    print(f"UNSIGNED CANDIDATE: {count} signals; {evidence} R43 evidence rows; "
          "0 topology rows. No SHA-256 attestation or release.")

if __name__ == "__main__":
    main()
