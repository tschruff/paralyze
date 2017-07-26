from unittest import TestCase
from paralyze.workspace import *


class WorkspaceTests(TestCase):

    def test_rdict(self):

        rdata = ReplacementDict({
            'x': 'some',
            'y': 'more',
            'text': 'Give me {x} {y}!',
            'nested.x': '{x}',
            'nested.y': '{other.x}',
            'other.x': '{y}',
            'z': '{nested.x}',
            'misc': dict(a='{x}', b=4, c=dict(x='{y}'), x={'x.x': '{x}'}),
            'a.b.c.d': 'Yes',
            'shout': '{a.b.c.d}, we can!',
            'f': '{g}',
            'g': '{f}',
            'var': '{v1} {v2}'
        }, namespace_separator='.')

        self.assertEqual(len(rdata), 16)

        # access items via [] operator
        self.assertEqual(rdata['text'], 'Give me some more!')
        self.assertEqual(rdata['nested']['x'], rdata['x'])
        self.assertEqual(rdata['nested.y'], rdata['other']['x'])
        self.assertEqual(rdata['nested.x'], rdata['z'])
        self.assertEqual(rdata['misc']['a'], 'some')
        self.assertEqual(rdata['misc.c.x'], rdata['y'])
        self.assertEqual(rdata['misc.x.x.x'], rdata['x'])
        self.assertEqual(rdata['a']['b']['c']['d'], rdata['a.b.c.d'])
        self.assertEqual(rdata['shout'], 'Yes, we can!')

        with self.assertRaises(RecursionError):
            print(rdata['f'])

        self.assertFalse(rdata.is_valid())
        del rdata['f']
        del rdata['g']

        self.assertEqual(len(rdata.fields()), 7)
        self.assertEqual(len(rdata.vars()), 2)
        del rdata['var']

        ns = rdata['nested']
        self.assertEqual(ns['x'], rdata['z'])
        self.assertEqual(ns['y'], rdata['other.x'])

        ns = rdata['a.b']
        self.assertEqual(ns['c.d'], 'Yes')

        self.assertEqual(len(rdata.formatted()), 13)
        self.assertTrue(rdata.is_valid())

        print(rdata.namespaces())
        self.assertEqual(len(rdata.namespaces()), 6)
        self.assertEqual(len(rdata['misc'].namespaces()), 2)


if __name__ == '__main__':
    import unittest
    unittest.main()
