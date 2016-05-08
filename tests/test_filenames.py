from datetime import datetime
import unittest

import msutils


class TestPageNameParsing(unittest.TestCase):
    """Test the parse_page_name function"""

    def test_simple_indd_filename(self):
        """parse_page_name correctly parses simple front InDesign file"""
        filename = '1_Front_040516.indd'
        expected = {'pages': (1,),
                    'section': 'Front',
                    'date': datetime(2016, 5, 4)}
        result = msutils.parse_page_name(filename)
        self.assertEqual(expected, result)

    def test_clearly_invalid_filename(self):
        """parse_page_name should raise ValueError with invalid filename"""
        filename = 'not a filename'
        with self.assertRaisesRegex(ValueError, 'not a valid filename'):
            msutils.parse_page_name(filename)

    def test_too_many_numbers_in_date(self):
        """Raise ValueError if date is not 6 numbers long"""
        filename = '1_Front_0400516.indd'
        with self.assertRaisesRegex(ValueError, 'not a valid filename'):
            msutils.parse_page_name(filename)

    def test_extra_underscore_in_section(self):
        """Correctly parse filename with underscore in section"""
        filename = '4-5_advert_Home_280414.indd'
        expected = {'pages': (4, 5),
                    'section': 'advert_Home',
                    'date': datetime(2014, 4, 28)}
        result = msutils.parse_page_name(filename)
        self.assertEqual(expected, result)

    def test_hyphen_as_separator(self):
        """Correctly parse filename with hyphen as separator"""
        filename = '10-11-FEATURES-251014.indd'
        expected = {'pages': (10, 11),
                    'section': 'FEATURES',
                    'date': datetime(2014, 10, 25)}
        result = msutils.parse_page_name(filename)
        self.assertEqual(expected, result)

    def test_space_as_separator(self):
        """Correctly parse filename with space as separator"""
        filename = '14-15 Features 150314.indd'
        expected = {'pages': (14, 15),
                    'section': 'Features',
                    'date': datetime(2014, 3, 15)}
        result = msutils.parse_page_name(filename)
        self.assertEqual(expected, result)

    def test_multiple_separator_chars(self):
        """Extra separator chars are excluded from section name"""
        filename = '11_Arts_ 231214.indd'
        expected = {'pages': (11,),
                    'section': 'Arts',
                    'date': datetime(2014, 12, 23)}
        result = msutils.parse_page_name(filename)
        self.assertEqual(expected, result)

    def test_known_invalid_no_date(self):
        """Filenames with no date raise ValueError"""
        filenames = ['14-15 Features.indd',
                     '17_Shares ad.indd']
        for fn in filenames:
            with self.assertRaisesRegex(ValueError, 'not a valid filename'):
                msutils.parse_page_name(fn)

    def test_known_invalid_5digit_date(self):
        """Filenames with ambiguous 5-digit date raise ValueError"""
        filenames = ['11_Arts_26314.indd',
                     '16-17_Arts_14115.indd',
                     '16-17_Arts_21115.indd',
                     '16-17_Arts_28115.indd']
        for fn in filenames:
            with self.assertRaisesRegex(ValueError, 'not a valid filename'):
                msutils.parse_page_name(fn)


if __name__ == '__main__':
    unittest.main(verbosity=2)
