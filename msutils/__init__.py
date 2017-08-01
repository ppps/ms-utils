from datetime import datetime
from pathlib import Path
import re


class Page(object):
    """Represents a page file on disk.

    Can be used for both InDesign (.indd) and PDF files.
    """

    _page_name_regex = re.compile('''\
    ^
    (?P<prefix> [a-zA-Z]* )
    (?P<first_page>  \d+)
    (?: -
        (?P<second_page> \d+)
    )?
    [-_ ]*
    (?P<section> \D+? )
    [-_ ]*
    (?P<date> \d{6} | \d{2}-\d{2}-\d{2,4} )
    \.
    (?P<type> \w+ )
    $
    ''', flags=re.VERBOSE)

    _page_date_format = '%d%m%y'

    _external_template = 'MS_{date:%Y}_{date:%m}_{date:%d}_{page:03}.{type}'

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
        if len(date_match) == 8:
            date_match = date_match[:-4] + date_match[-2:]

        self.date = datetime.strptime(date_match, self._page_date_format)

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

    def external_name(self):
        """Returns string used outside the Star to identify the page

        Raises ValueError if called on instances representing a file
        representing more than a single page.
        """
        if len(self.pages) > 1:
            raise ValueError(
                'external_name is invalid for Page instances that represent'
                'multiple pages'
                )
        return self._external_template.format(
            date=self.date,
            page=self.pages[0],
            type=self.type)
