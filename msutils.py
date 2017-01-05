from datetime import datetime
from pathlib import Path
import re

def parse_page_name(name):
    """Extract page, section and date from a filename

    Returns a dict of the form:
        {
            'pages': tuple of ints (length 1 or 2),
            'section': string,
            'date': datetime object
        }
    """
    page_name_regex = re.compile('''\
        ^
        (?P<first_page>  \d+)
        -?
        (?P<second_page> \d+)?
        [-_ ]+
        (?P<section> .+? )
        [-_ ]+
        (?P<date> \d{6} )
        \.
    ''', flags=re.VERBOSE)
    try:
        groups = page_name_regex.match(name).groupdict()
    except AttributeError:
        raise ValueError('{0} is not a valid filename'.format(name))

    pages = [groups['first_page']]
    if groups['second_page'] is not None:
        pages.append(groups['second_page'])
    pages = tuple(map(int, pages))

    date = datetime.strptime(groups['date'], '%d%m%y')

    return {'pages': pages,
            'section': groups['section'],
            'date': date}


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
            raise ValueError('Page does not have a valid name')

        pages = [regex_match['first_page']]
        if regex_match['second_page'] is not None:
            pages.append(regex_match['second_page'])
        self.pages = tuple(map(int, pages))


        self.date = datetime.strptime(regex_match['date'],
                                       self._page_date_format)
        self.section = regex_match['section']
        self.type = regex_match['type'].lower()
