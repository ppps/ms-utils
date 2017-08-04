from datetime import datetime
from pathlib import Path
import unittest

from hypothesis import given, example
import hypothesis.strategies as st

import msutils

TEST_DIR = Path(__file__).parent

good_names_dir = Path(TEST_DIR, 'sample-names/pass')
bad_names_dir = Path(TEST_DIR, 'sample-names/fail')
filter_txt = lambda d: (p for p in d.iterdir() if p.suffix == '.txt')
GOOD_NAMES = []
BAD_NAMES = []
for file in filter_txt(good_names_dir):
    with open(file, encoding='utf-8') as names_file:
        for line in names_file:
            GOOD_NAMES.append(line.rstrip())

for file in filter_txt(bad_names_dir):
    with open(file, encoding='utf-8') as names_file:
        for line in names_file:
            BAD_NAMES.append(line.rstrip())


class TestPageNameParsing(unittest.TestCase):
    """Test Page correctly constructed from file path"""

    def test_simple_indd_filename(self):
        """Page correctly parses simple front InDesign file"""
        filename = Path('1_Front_040516.indd')
        expected = {'pages': (1,),
                    'section': 'Front',
                    'date': datetime(2016, 5, 4)}
        result = msutils.Page(filename)
        for attr, value in expected.items():
            self.assertEqual(value, getattr(result, attr))

    def test_clearly_invalid_filename(self):
        """Page should raise ValueError with invalid filename"""
        filename = Path('not a filename')
        with self.assertRaisesRegex(ValueError, 'invalid filename'):
            msutils.Page(filename)

    def test_too_many_numbers_in_date(self):
        """Raise ValueError if date is not 6 numbers long"""
        filename = Path('1_Front_0400516.indd')
        with self.assertRaisesRegex(ValueError, 'invalid filename'):
            msutils.Page(filename)

    def test_extra_underscore_in_section(self):
        """Correctly parse filename with underscore in section"""
        filename = Path('4-5_advert_Home_280414.indd')
        expected = {'pages': (4, 5),
                    'section': 'advert_Home',
                    'date': datetime(2014, 4, 28)}
        result = msutils.Page(filename)
        for attr, value in expected.items():
            self.assertEqual(value, getattr(result, attr))

    def test_hyphen_as_separator(self):
        """Correctly parse filename with hyphen as separator"""
        filename = Path('10-11-FEATURES-251014.indd')
        expected = {'pages': (10, 11),
                    'section': 'FEATURES',
                    'date': datetime(2014, 10, 25)}
        result = msutils.Page(filename)
        for attr, value in expected.items():
            self.assertEqual(value, getattr(result, attr))

    def test_space_as_separator(self):
        """Correctly parse filename with space as separator"""
        filename = Path('14-15 Features 150314.indd')
        expected = {'pages': (14, 15),
                    'section': 'Features',
                    'date': datetime(2014, 3, 15)}
        result = msutils.Page(filename)
        for attr, value in expected.items():
            self.assertEqual(value, getattr(result, attr))

    def test_multiple_separator_chars(self):
        """Extra separator chars are excluded from section name"""
        filename = Path('11_Arts_ 231214.indd')
        expected = {'pages': (11,),
                    'section': 'Arts',
                    'date': datetime(2014, 12, 23)}
        result = msutils.Page(filename)
        for attr, value in expected.items():
            self.assertEqual(value, getattr(result, attr))

    def test_known_invalid_no_date(self):
        """Filenames with no date raise ValueError"""
        filenames = ['14-15 Features.indd',
                     '17_Shares ad.indd']
        for fn in filenames:
            with self.assertRaisesRegex(ValueError, 'invalid filename'):
                msutils.Page(Path(fn))

    def test_known_invalid_5digit_date(self):
        """Filenames with ambiguous 5-digit date raise ValueError"""
        filenames = ['11_Arts_26314.indd',
                     '16-17_Arts_14115.indd',
                     '16-17_Arts_21115.indd',
                     '16-17_Arts_28115.indd']
        for fn in filenames:
            with self.assertRaisesRegex(ValueError, 'invalid filename'):
                msutils.Page(Path(fn))


class TestPageMisc(unittest.TestCase):
    """Test non-page-parsing aspects of Page"""

    def test_path_stored_name_only(self):
        """Page correctly stores a name-only path"""
        p = Path('1_Front_040516.indd')
        result = msutils.Page(p)
        self.assertEqual(p, result.path)

    def test_path_stored_full_path(self):
        """Page correctly stores full path supplied in constructor"""
        p = Path('/fake/but/full/path/1_Front_040516.indd')
        result = msutils.Page(p)
        self.assertEqual(p, result.path)

    def test_path_user_expanded(self):
        """Page expands ~ in supplied path"""
        p = Path('~/fake/pages/dir/1_Front_040516.indd')
        result = msutils.Page(p)
        self.assertEqual(p.expanduser(), result.path)

    def test_type_stored_indd(self):
        """Page correctly stores 'indd' under .type"""
        page = msutils.Page(Path('1_Front_040516.indd'))
        self.assertEqual('indd', page.type)

    def test_type_stored_pdf(self):
        """Page correctly stores 'indd' under .type"""
        page = msutils.Page(Path('1_Front_040516.pdf'))
        self.assertEqual('pdf', page.type)

    def test_type_stored_lower(self):
        """Page correctly lowercases the file's type"""
        page = msutils.Page(Path('1_Front_040516.INDD'))
        self.assertEqual('indd', page.type)

    def test_prefix_stored(self):
        """Page stores any prefix in the filename"""
        page = msutils.Page(Path('W4_Back_240314.indd'))
        self.assertEqual(page.prefix, 'W')

    def test_str(self):
        """Page returns original filename for __str__"""
        orig_path = Path('1_Front_040516.indd')
        page = msutils.Page(orig_path)
        self.assertEqual(orig_path.name, str(page))

    def test_repr(self):
        """Page returns 'Page(page.path)' for __repr__"""
        orig_path = Path('/test/path/1_Front_040516.indd')
        page = msutils.Page(orig_path)
        self.assertEqual(
            'Page({})'.format(repr(orig_path)),
            repr(page)
            )


class TestPageExternalName(unittest.TestCase):
    """Test Page.external_name method

    Returns a string suitable for use by external partners. These names
    omit the section and are formatted such that they sort by date when
    listed alphabetically.

    It should only be used for single-page files and raises a ValueError
    if used called on a Page object representing a file that contains
    more than a single page.

    Our canonical (as of the start of 2017) external name format for
    single pages is:
        MS_2017_01_31_000

    .external_name should format Pages to this scheme and include the
    Page's type. This function is typically used for PDF files but the
    function should not assume it.
    """

    def test_basic_case_indd(self):
        """external_name formats a known correct InDesign page"""
        page = msutils.Page(Path('1_Front_040516.indd'))
        expected = 'MS_2016_05_04_001.indd'
        self.assertEqual(page.external_name(),
                         expected)

    def test_basic_case_pdf(self):
        """external_name formats a known correct InDesign page"""
        page = msutils.Page(Path('1_Front_040516.pdf'))
        expected = 'MS_2016_05_04_001.pdf'
        self.assertEqual(page.external_name(),
                         expected)

    def test_multiple_pages_raises(self):
        """external_name raises ValueError for non-single pages"""
        page = msutils.Page(Path('2-3_Home_040516.indd'))
        with self.assertRaisesRegex(ValueError, 'multiple pages'):
            page.external_name()


class TestPageUsingHypothesis(unittest.TestCase):
    """Property-based testing with Hypothesis"""

    @example('1_Front_03082017.indd')    # Allow 8-digit dates unhyphenated
    @example('W4_Back_240314.indd')      # Allow prefixes
    @given(st.sampled_from(GOOD_NAMES))
    def test_Page_accepts_known_good(self, name):
        """Page should accept known-good names from a corpus"""
        page = msutils.Page(page_path=Path(name))

    @example('10_film29-02-03.indd')
    @example('18_advertisement2_280415.indd')
    @given(st.sampled_from(BAD_NAMES))
    def test_Page_rejects_known_bad(self, name):
        """Page should reject known-bad names from a corpus"""
        with self.assertRaises(ValueError):
            msutils.Page(page_path=Path(name))

    @st.composite
    def _page_name_with_comparators(draw):
        """Hypothesis strategy that returns a page name and its key parts

        This strategy provides a tuple as such:
            ('1_Front_311229.indd',      # page name
             (datetime(1929, 12, 31),    # edition date
              'indd',                    # file type
              '',                        # prefix
              1,                         # page number (left-hand if spread)
              'front')                   # section (.lower())
             )

        The intention is that the page name can be used as an
        argument to Page, and the tuple of represented elements
        is used as a sorting key.

        The order above might appear odd at first glance, but it
        achieves the following:
            * Each edition's files are grouped together (date)
            * Each type of page is grouped together (indd/pdf)
            * Within each type, prefixes are grouped (including '')
            * Then the page ordering comes into effect
            * Lastly the section is included, lowered, for alphabetical sort
              (It is unlikely the section would ever be needed, and is
              probably actually a sign that something has gone wrong.)

        This would provide the following order:
            1_Front_200129.indd
            2_Home_200129.indd
            1_Front_200129.pdf
            2_Home_200129.pdf
            1_Front_210129.indd
            2_Home_210129.indd
           A1_Insert_210129.indd
           A2_Insert_210129.indd
            1_Front_210129.pdf
            2_Home_210129.pdf
           A1_Insert_210129.pdf
           A2_Insert_210129.pdf

        (Note: 1929 is used as an example here, as it was the year before
        the Daily Worker was first published, but the date range generated
        is constrained to stop problems arising with the use of the six-
        digit date being parsed and datetime assuming the wrong century.

        This is judged to be acceptable because the domain for these pages
        is the computer files used to publish the Morning Star, for which
        we only have files going back to 2002 — and the earlier editions in
        this range don't consist of single files that could be represented
        by the Page class.)
        """
        pass

    # This horrendous decorator is being replaced
    # by the composite function above

    @given(
        st.integers(min_value=1, max_value=100),
        st.datetimes(),
        st.sampled_from(['Home', 'Foreign', 'Features', 'Arts', 'Sport']),
        st.integers(min_value=1, max_value=100),
        st.datetimes())
    def test_Page_equal(self, *args):
        pass

if __name__ == '__main__':
    unittest.main(verbosity=2)
