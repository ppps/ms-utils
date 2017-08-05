from datetime import datetime
from pathlib import Path
import re


class Page(object):
    """Represents a page file on disk.

    Can be used for both InDesign (.indd) and PDF files.
    """

    _page_name_regex = re.compile('''\
    ^
    (?P<prefix> [A-Z]{0,1} )
    (?P<first_page>  \d+)
    (?: -
        (?P<second_page> \d+)
    )?
    [-_ ]*
    (?P<section> \D+? )
    [-_ ]*
    (?P<date> \d{6} | \d{8} | \d{2}-\d{2}-\d{2,4} )
    \.
    (?P<type> indd | pdf )
    $
    ''', flags=re.VERBOSE | re.IGNORECASE)

    _page_date_format = '%d%m%y'

    def __init__(self, page_path: Path):
        """Set up Page from a path to a file on disk

        page_path:  pathlib.Path object

        The page stored at page_path should be named according to the
        usual Morning Star convention, described in this class's
        page_name_regex pattern.
        """
        regex_match = self._page_name_regex.match(page_path.name)
        if not regex_match:
            raise ValueError(f'{page_path.name} is an invalid filename')

        self.path = page_path.expanduser()

        pages = [regex_match['first_page']]
        if regex_match['second_page'] is not None:
            pages.append(regex_match['second_page'])
        self.pages = tuple(map(int, pages))

        date_match = regex_match['date'].replace('-', '')
        if len(date_match) == 6:
            date_format = '%d%m%y'
        elif len(date_match) == 8:
            date_format = '%d%m%Y'
        else:
            raise ValueError("Page's date does not have 6 or 8 digits")

        self.date = datetime.strptime(date_match, date_format).date()

        self.prefix = regex_match['prefix']
        self.section = regex_match['section']
        self.type = regex_match['type'].lower()

    def __str__(self):
        """Return the name of the underlying file"""
        return self.path.name

    def __repr__(self):
        """Return string Page(Path(…))"""
        return '{0}({1})'.format(self.__class__.__name__,
                                 repr(self.path))

    @staticmethod
    def _comparison_keys(page):
        """Return list of important attributes for comparisons"""
        return (page.date, page.type, page.prefix,
                page.pages, page.section.lower())

    def __eq__(self, other):
        """Test for equality against another Page

        The following attributes are considered, in this order:
            * date
            * type
            * prefix
            * pages[0] (right-hand page number is ignored)
            * section (case-insensitively)
        """
        return self._comparison_keys(self) == self._comparison_keys(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self._comparison_keys(self) < self._comparison_keys(other)

    def __gt__(self, other):
        return self._comparison_keys(self) > self._comparison_keys(other)

    def __le__(self, other):
        return (self.__lt__(other) or self.__eq__(other))

    def __ge__(self, other):
        return (self.__ge__(other) or self.__eq__(other))

    def external_name(self):
        """Returns string used outside the Star to identify the page

        For single pages without a prefix:
            MS_1929_12_31_001.pdf
        Where that is MS, year, month, date, page number and file extension.

        For multiple pages without a prefix:
            MS_1929_12_31_002-003.indd

        For single pages with a prefix:
            MS_1929_12_31_A_001.pdf
        Where the prefix comes before the page number.

        For multiple pages with a prefix:
            MS_1929_12_31_A_002-003.indd
        """
        if not self.prefix:
            template = 'MS_{date:%Y_%m_%d}_{nums}.{suffix}'
        else:
            template = 'MS_{date:%Y_%m_%d}_{prefix}_{nums}.{suffix}'

        num_str = '-'.join(f'{p:03}' for p in self.pages)

        return template.format(
            date=self.date, prefix=self.prefix, suffix=self.type,
            nums=num_str)
