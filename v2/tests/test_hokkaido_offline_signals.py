#!/usr/bin/env python3
"""New-scope-only tests (NOT EXECUTED under stage 1-4-1-5-33)."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'signals/offline/build_hokkaido_signals.py'
spec = importlib.util.spec_from_file_location('cb6_offline_builder', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ConfirmedTopologyTests(unittest.TestCase):
    def test_shared_real_osm_junction_can_group(self):
        # A road graph with two signal nodes joining the SAME 3-branch OSM node.
        pos = {1:(43.,141.0000),2:(43.,141.0001),3:(43.,141.0002),
               4:(43.0001,141.0001),5:(42.9999,141.0001)}
        edges = {(1,2),(2,3),(2,4),(2,5)}
        # Road ways 101: 1-2-3 and 102: 4-2-5 share junction node 2.
        node_road_ways = {1:{101},2:{101,102},3:{101},4:{102},5:{102}}
        groups = module.derive_confirmed_groups({1:pos[1],3:pos[3]},edges,pos,node_road_ways)
        self.assertEqual(groups[1][0],2)
        self.assertEqual(groups[3][0],2)
    def test_two_nearby_unconnected_ways_do_not_group(self):
        pos={1:(43.,141.),2:(43.,141.00005),11:(43.,141.0001),
             12:(43.,141.00015)}
        edges={(1,2),(11,12)}
        # Road ways 101: 1-2 and 102: 11-12 have no shared node.
        node_road_ways = {1:{101},2:{101},11:{102},12:{102}}
        self.assertEqual(module.derive_confirmed_groups({1:pos[1],11:pos[11]},edges,pos,node_road_ways),{})
    def test_ambiguous_multiple_junctions_remain_visible(self):
        pos={i:(43.,141.+i*0.00001) for i in range(1,9)}
        edges={(1,2),(2,3),(2,4),(4,5),(5,6),(5,7),(7,8)}
        # Signal node 4 is within reach of two junctions: no 200 m thinning.
        # Ways 101: 1-2-3, 102: 2-4-5-6, 103: 5-7-8 certify nodes 2 and 5.
        node_road_ways = {1:{101},2:{101,102},3:{101},4:{102},
                          5:{102,103},6:{102},7:{103},8:{103}}
        self.assertNotIn(4,module.derive_confirmed_groups({4:pos[4],8:pos[8]},edges,pos,node_road_ways))
    def test_fixed_input_source_is_pinned(self):
        self.assertEqual(module.FIXED_PBF_SIZE,189578209)
        self.assertEqual(module.FIXED_PBF_SHA256,
          '2e4ac16f5b269624a36e3087c10466e080a71185de3440c488e188ef55320726')
    def test_no_key_or_network_operations_in_builder(self):
        src=SOURCE.read_text()
        for forbidden in ('requests.get(', 'subprocess.run(', 'git push', 'BEGIN PRIVATE KEY'):
            self.assertNotIn(forbidden,src)

if __name__ == '__main__':
    unittest.main()
