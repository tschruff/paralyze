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

    def test_config_1(self):

        settings = {
            "y": "{{ x|int }}",
            "z": "{{ nested['z'] }}",
            "nested": {
                "x": "{{ x }}",
                "y": "{{ 2 * x }}",
                "z": "{{ y }}"
            },
            "other_nested": {
                "x": "{{ nested['z'] }}",
                "y": "{{ nested.y }}"
            }
        }

        config = Configuration(settings)
        values = config.render(x=3)

        self.assertEqual(values['y'], '3')
        self.assertEqual(values['nested']['y'], '6')
        self.assertEqual(values['nested']['z'], '3')
        self.assertEqual(values['nested']['x'], '3')
        self.assertEqual(values['other_nested']['x'], '3')
        self.assertEqual(values['other_nested']['y'], '6')

        values = config.render(x=6)

        self.assertEqual(values['y'], '6')
        self.assertEqual(values['nested']['y'], '12')
        self.assertEqual(values['nested']['z'], '6')
        self.assertEqual(values['nested']['x'], '6')
        self.assertEqual(values['other_nested']['x'], '6')
        self.assertEqual(values['other_nested']['y'], '12')

    def test_config_2(self):

        settings = {
            "a": "{{ variables.x }}",
            "b": "{{ variables.x + variables.y }}",
            "c": "{{ a }}"
        }

        config = Configuration(settings)
        config = config.finalize(variables={'x': 1, 'y': 2})

        with self.assertRaises(KeyError):
            print(config['e'])

        self.assertEqual(int(config['a']), 1)
        self.assertEqual(int(config['b']), 3)
        self.assertEqual(int(config['c']), 1)


if __name__ == '__main__':
    import unittest
    unittest.main()
