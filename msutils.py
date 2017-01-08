from datetime import datetime
from pathlib import Path
import re


class Page(object):
    """Represents a page file on disk.

    Can be used for both InDesign (.indd) and PDF files.
    """

    _page_name_regex = re.compile('''\
    ^
    (?P<first_page>  \d+)
    (?: -
        (?P<second_page> \d+)
    )?
    [-_ ]+
    (?P<section> .+? )
    [-_ ]+
    (?P<date> \d{6} )
    \.
    (?P<type> \w+ )
    ''', flags=re.VERBOSE)

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
            raise ValueError(
                '{0} is an invalid filename'.format(page_path.name))

        self.path = page_path

        pages = [regex_match['first_page']]
        if regex_match['second_page'] is not None:
            pages.append(regex_match['second_page'])
        self.pages = tuple(map(int, pages))

        self.date = datetime.strptime(regex_match['date'],
                                      self._page_date_format)
        self.section = regex_match['section']
        self.type = regex_match['type'].lower()
