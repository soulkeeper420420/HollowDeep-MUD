import unittest
from build_ad_builder_driver import build


class BuilderDriver(unittest.TestCase):
    def source(self):
        return ('def in_game(text):\n    return bool(re.search("old",text))\n'
                'elif "54 points" in low and "stats" in low:\n'
                '    answer = "12 11 11 10 10"\n'
                '        elif "weapons proficiency" in low:\n')

    def test_both_stat_prompts_keep_the_valid_54_point_distribution(self):
        result=build(self.source())
        self.assertIn('"65 total points" in low',result)
        self.assertIn('"54 points" in low',result)
        self.assertIn('12 11 11 10 10',result)
        self.assertIn('enable ansi colors and colored status',result)
        self.assertIn('answer = "no"',result)

    def test_unreviewed_or_ambiguous_driver_refused(self):
        with self.assertRaises(ValueError): build('new driver')
        with self.assertRaises(ValueError):
            build('elif "54 points" in low and "stats" in low:\n'*2)


if __name__=='__main__': unittest.main()
