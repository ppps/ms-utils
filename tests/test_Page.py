from datetime import date, timedelta
from pathlib import Path
import string
import unittest

from hypothesis import given, example, assume
import hypothesis.strategies as st

import msutils

TEST_DIR = Path(__file__).parent

good_names_dir = Path(TEST_DIR, 'sample-names/pass')
bad_names_dir = Path(TEST_DIR, 'sample-names/fail')


def filter_txt(directory):
    for path in directory.iterdir():
        if path.suffix == '.txt':
            yield path


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


def _make_page_name(prefix, page_nums, section, page_date, suffix):
    """Return a formatted page name"""
    num_str = '-'.join(map(str, page_nums))
    return f'{prefix}{num_str}_{section}{page_date:%d%m%y}.{suffix}'


class TestPageNameParsing(unittest.TestCase):
    """Test Page correctly constructed from file path"""

    def test_simple_indd_filename(self):
        """Page correctly parses simple front InDesign file"""
        filename = Path('1_Front_040516.indd')
        expected = {'pages': (1,),
                    'section': 'Front',
                    'date': date(2016, 5, 4)}
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
                    'date': date(2014, 4, 28)}
        result = msutils.Page(filename)
        for attr, value in expected.items():
            self.assertEqual(value, getattr(result, attr))

    def test_hyphen_as_separator(self):
        """Correctly parse filename with hyphen as separator"""
        filename = Path('10-11-FEATURES-251014.indd')
        expected = {'pages': (10, 11),
                    'section': 'FEATURES',
                    'date': date(2014, 10, 25)}
        result = msutils.Page(filename)
        for attr, value in expected.items():
            self.assertEqual(value, getattr(result, attr))

    def test_space_as_separator(self):
        """Correctly parse filename with space as separator"""
        filename = Path('14-15 Features 150314.indd')
        expected = {'pages': (14, 15),
                    'section': 'Features',
                    'date': date(2014, 3, 15)}
        result = msutils.Page(filename)
        for attr, value in expected.items():
            self.assertEqual(value, getattr(result, attr))

    def test_multiple_separator_chars(self):
        """Extra separator chars are excluded from section name"""
        filename = Path('11_Arts_ 231214.indd')
        expected = {'pages': (11,),
                    'section': 'Arts',
                    'date': date(2014, 12, 23)}
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

    def test_multiple_pages(self):
        """external_name correctly formats non-single pages"""
        page = msutils.Page(Path('2-3_Home_040516.indd'))
        expected = 'MS_2016_05_04_002-003.indd'
        self.assertEqual(
            page.external_name(),
            expected)


class TestPageUsingHypothesis(unittest.TestCase):
    """Property-based testing with Hypothesis"""

    @st.composite
    def _page_name_with_elements(draw):
        """Hypothesis strategy that returns a page name and its key parts

        This strategy provides a tuple as such:
            (Path('1_Front_311229.indd'),   # page name as Path
             (date(1929, 12, 31),           # edition date
              'indd',                       # file type
              '',                           # prefix
              1,                            # page number (left-hand if spread)
              'front')                      # section (.lower())
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
        # Strategy that has no numbers and no control characters
        # No numbers so that it matches \D (for the section)
        # No control characters to head off any headaches
        # (We're not testing the text handling here.)
        # Po is included to exclude slashes (which are parsed as
        # directory separators by pathlib).
        num_control_cats = ['Po', 'Nd', 'Nl', 'No',
                            'Cc', 'Cf', 'Cs', 'Co', 'Cn']
        text_no_nums_or_control = st.text(
            alphabet=st.characters(blacklist_categories=num_control_cats),
            min_size=1, max_size=16)

        section = draw(text_no_nums_or_control)
        # Page strips separator characters from the section name, so
        # hypothesis shouldn't complain when they don't show up later.
        #
        # We assume that section is not the empty string when they're
        # stripped, but don't strip them from the section itself as
        # it's perfectly fine to include them.
        #
        # They are however stripped from the section comparison key
        # in the tuple that is returned.
        #
        # The generation of the section is higher up than it otherwise
        # might be to save us a bit of time if assume causes hypothesis
        # to bail on the strategy and try again.
        assume(section.strip(' -_'))

        # Either the empty string or a single uppercase ASCII letter
        prefix = draw(st.one_of(
            st.just(''),
            st.sampled_from(string.ascii_uppercase)))

        num_1 = draw(st.integers(min_value=1, max_value=100))
        if (not num_1 % 2) and draw(st.booleans()):
            num_2 = num_1 + 1
            p_nums = (num_1, num_2)
        else:
            num_2 = None
            p_nums = (num_1,)

        p_date = draw(st.dates(
            min_date=date(2000, 1, 1),
            max_date=date(2033, 1, 1)))
        suffix = draw(st.sampled_from(['pdf', 'indd']))

        page_name = _make_page_name(prefix, p_nums, section, p_date, suffix)

        return (Path(page_name),
                (p_date, suffix, prefix, p_nums,
                 section.lower().strip(' -_')))

    @example('1_Front_03082017.indd')    # Allow 8-digit dates unhyphenated
    @example('W4_Back_240314.indd')      # Allow prefixes
    @given(st.sampled_from(GOOD_NAMES))
    def test_Page_accepts_known_good(self, name):
        """Page should accept known-good names from a corpus

        No assertions here, as Page will raise a ValueError
        """
        try:
            msutils.Page(page_path=Path(name))
        except ValueError as e:
            self.fail(e)

    @example('10_film29-02-03.indd')
    @example('18_advertisement2_280415.indd')
    @given(st.sampled_from(BAD_NAMES))
    def test_Page_rejects_known_bad(self, name):
        """Page should reject known-bad names from a corpus"""
        with self.assertRaises(ValueError):
            msutils.Page(page_path=Path(name))

    @given(_page_name_with_elements())
    def test_Page_self_equal(self, arg_tuple):
        """Pages that have matching attributes compare equal

        In this case, we instantiate two Pages with the same path
        and assert that they should compare equal to each other.

        Page should compare on the following, in this order:
            * Date
            * Type (file extension)
            * Prefix
            * Page number (left-hand if a spread)
            * Section (case-insensitively)
        """
        page_path, _ = arg_tuple
        page_1 = msutils.Page(page_path)
        page_2 = msutils.Page(page_path)
        self.assertEqual(page_1, page_2)

    @given(_page_name_with_elements(),
           _page_name_with_elements())
    def test_Page_two_equal(self, page1_tuple, page2_tuple):
        """Pages instantiated from the same path are the same

        In this case, we instantiate two Pages with different paths
        and assert that they should compare equal to each other if
        and only if their list comparison keys compare equal.
        """
        p1_path, p1_list = page1_tuple
        p2_path, p2_list = page2_tuple
        page_1 = msutils.Page(p1_path)
        page_2 = msutils.Page(p2_path)

        if p1_list == p2_list:
            self.assertEqual(page_1, page_2)
        else:
            self.assertNotEqual(page_1, page_2)

    @given(_page_name_with_elements(),
           _page_name_with_elements())
    def test_Page_compare_lt_gt(self, page1_tuple, page2_tuple):
        """Pages sort according to their comparison keys

        In this case, we instantiate two Pages with different paths
        and assert that they should compare less than or greater
        than based on how their list comparison keys compare.
        """
        p1_path, p1_list = page1_tuple
        p2_path, p2_list = page2_tuple

        assume(p1_list != p2_list)  # Skip test if the pages are equal

        page_1 = msutils.Page(p1_path)
        page_2 = msutils.Page(p2_path)

        if p1_list < p2_list:
            self.assertLess(page_1, page_2)
        elif p1_list > p2_list:
            self.assertGreater(page_1, page_2)

    @given(_page_name_with_elements())
    def test_Page_compare_le(self, page_tuple):
        """Compare pages using <= operator"""
        page_name, (page_date, suffix, prefix, page_nums, section) = page_tuple
        page_1 = msutils.Page(page_name)
        page_2 = msutils.Page(
            Path(_make_page_name(prefix, page_nums, section,
                                 page_date + timedelta(1),
                                 suffix)))
        self.assertLessEqual(page_1, page_1)
        self.assertLessEqual(page_1, page_2)

    @given(_page_name_with_elements())
    def test_Page_compare_ge(self, page_tuple):
        """Compare pages using >= operator"""
        page_name, (page_date, suffix, prefix, page_nums, section) = page_tuple
        page_1 = msutils.Page(page_name)
        page_2 = msutils.Page(
            Path(_make_page_name(prefix, page_nums, section,
                                 page_date + timedelta(1),
                                 suffix)))
        self.assertGreaterEqual(page_1, page_1)
        self.assertGreaterEqual(page_2, page_1)

    @given(_page_name_with_elements())
    def test_Page_comparison_keys(self, arg_tuple):
        page_path, keys = arg_tuple
        page = msutils.Page(page_path)
        self.assertEqual(
            msutils.Page._comparison_keys(page),
            keys)

    @given(_page_name_with_elements())
    def test_Page_external_name(self, page_tuple):
        """external_name formats as expected

        For single pages without a prefix:
            MS_1929_12_31_001.pdf
        Where that is MS, %Y, %m, %d, page number and file extension.

        For multiple pages without a prefix:
            MS_1929_12_31_002-003.indd

        For single pages with a prefix:
            MS_A_1929_12_31_001.pdf
        Where the prefix comes before the page number.

        For multiple pages with a prefix:
            MS_A_1929_12_31_002-003.indd
        """
        name, (p_date, suffix, prefix, p_nums, _) = page_tuple
        page = msutils.Page(name)

        nums_str = '-'.join(f'{n:03}' for n in p_nums)
        formatted = f'MS_{prefix}_{p_date:%Y_%m_%d}_{nums_str}.{suffix}'
        formatted = formatted.replace('__', '_')

        self.assertEqual(page.external_name(), formatted)


if __name__ == '__main__':
    unittest.main(verbosity=2)
