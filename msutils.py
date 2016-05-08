from datetime import datetime
import re


def parse_page_name(name):
    """Extra page, section and date from a filename

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
        _
        (?P<section> .+ )
        _
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
