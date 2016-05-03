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
        with self.assertRaises(ValueError):
            msutils.parse_page_name(filename)


if __name__ == '__main__':
    unittest.main(verbosity=2)
