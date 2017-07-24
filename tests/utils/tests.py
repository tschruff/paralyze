"""Module documentation goes here...

"""
from unittest import TestCase
from paralyze.utils import *


class UtilsTests(TestCase):

    def test_nested_dict(self):

        mapping = {
            "a": {
                "a": {
                    "a": 1
                },
                "b": 2
            },
            "b": 3
        }

        nd = NestedDict(mapping)

        self.assertEqual(len(nd), 3)
        self.assertEqual(len(nd.keys()), 3)
        self.assertEqual(len(nd.values()), 3)
        self.assertEqual(len(nd.items()), 3)

        # getter
        self.assertEqual(nd['a.a.a'], 1)
        self.assertEqual(sum(nd[('a.a.a', 'a.b', 'b')]), 6)

        # setter
        nd['a.a.a'] = 3
        self.assertEqual(nd.pop('a.a.a'), 3)

        # copy
        nd2 = nd.copy()

        # compare equal
        self.assertEqual(nd, nd2)

        # clear
        nd2.clear()
        self.assertEqual(len(nd2), 0)

    def test_nested_config(self):

        settings = {
            "y": "{{ x }}",
            "z": "{{ nested.z }}",
            "nested": {
                "x": "{{ x }}",
                "y": "{{ x }}",
                "z": "{{ y }}"
            },
            "other_nested": {
                "x": "{{ nested.z }}",
                "y": "{{ nested.y }}"
            },
            "a": "{{ variables.x }}",
            "b": "{{ variables.y }}",
            "c": "{{ a }}"
        }

        config = ConfigDict(settings)
        values = config.render(x=3, variables={'x': 1, 'y': 2})

        self.assertEqual(len(config.variables()), 3)

        self.assertEqual(values['y'], '3')
        self.assertEqual(values['nested']['y'], '3')
        self.assertEqual(values['nested']['z'], '3')
        self.assertEqual(values['nested']['x'], '3')
        self.assertEqual(values['other_nested']['x'], '3')
        self.assertEqual(values['other_nested']['y'], '3')

        values = config.render(x=6, variables={'x': 1, 'y': 2})

        self.assertEqual(values['y'], '6')
        self.assertEqual(values['nested']['y'], '6')
        self.assertEqual(values['nested']['z'], '6')
        self.assertEqual(values['nested']['x'], '6')
        self.assertEqual(values['other_nested']['x'], '6')
        self.assertEqual(values['other_nested']['y'], '6')

        values = config.render(x=1, variables={'x': 1, 'y': 2})

        with self.assertRaises(KeyError):
            print(values['e'])

        self.assertEqual(int(values['a']), 1)
        self.assertEqual(int(values['b']), 2)
        self.assertEqual(int(values['c']), 1)


if __name__ == '__main__':
    import unittest
    unittest.main()
