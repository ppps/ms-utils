import logging
from pathlib import Path

from .page import Page

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

PAGES_ROOT = Path('~/Server/Pages/').expanduser()
CURRENT_EDITION_TEMPLATE = '{0:%Y-%m-%d %A %b %-d}'
ARCHIVE_EDITION_TEMPLATE = '{0:%Y/%m %B/%Y-%m-%d %A}'
PRESS_PDFS_TEMPLATE = '{0:PDFs %d%m%y}'
WEB_PDFS_TEMPLATE = '{0:E-edition PDFs %d%m%y}'

EDITION_STORES = [
    (Path('~/Server/Pages').expanduser(), CURRENT_EDITION_TEMPLATE),
    (Path('/Volumes/MS-T4-Archive-2002-2016'), ARCHIVE_EDITION_TEMPLATE),
    (Path('/Volumes/MS-T4-Archive-Since-2017'), ARCHIVE_EDITION_TEMPLATE),
    (Path('/Volumes/Server/Pages'), CURRENT_EDITION_TEMPLATE),
    (Path('/Volumes/Archive-2002-2016'), ARCHIVE_EDITION_TEMPLATE),
    (Path('/Volumes/Archive-Since-2017'), ARCHIVE_EDITION_TEMPLATE),
    ]


class NoEditionError(Exception):
    """No edition can be found for the given date"""
    pass


class NoEditionStoresError(Exception):
    """No edition stores are present on the system"""
    pass


def _fetch_stores():
    """Return paths to edition stores along with path templates

    Result is a list of tuples:
        [(path: Path, path_template: str)]

    Template is returned because of differences in where editions are
    stored when considered 'current' and when moved to the archive.
    """
    present_stores = [(path, ed_template)
                      for (path, ed_template) in EDITION_STORES
                      if path.exists()]
    logger.debug(
        'Connected stores:\n    %s',
        '\n    '.join(str(p) for p, t in present_stores))

    if present_stores:
        return present_stores
    else:
        raise NoEditionStoresError(
            'No edition stores are connected, either current or archive')


def edition_dir(date):
    """Return path to date's edition directory

    Raises NoEditionError if an edition can't be
    found in the expected locations for date.
    """
    present_stores = _fetch_stores()
    for store, path_template in present_stores:
        candidate = store.joinpath(path_template.format(date))
        if candidate.exists():
            logger.debug('Found edition dir: %s', candidate)
            return candidate
    else:
        raise NoEditionError(f'Cannot find edition for {date:%Y-%m-%d}')


def _paths_to_pages(paths):
    """Yield Pages from Paths, handling exceptions from non-Pages"""
    for p in paths:
        try:
            yield Page(p)
        except ValueError:
            continue


def directory_indd_files(path):
    """List all the InDesign files in the given directory

    This finds all .indd files in the directory and its subdirectories.

    This is unlike the PDF functions; it is because supplements and
    inserts are often kept in subdirectories instead of in the root
    of the edition directory.
    """
    return sorted(_paths_to_pages(path.rglob('*.indd')))


def edition_indd_files(date):
    """List InDesign Pages for date's edition"""
    return directory_indd_files(edition_dir(date))


def directory_pdfs(path):
    """List Page-acceptable PDFs in path"""
    # PDFs directory may not exist yet, even if the edition does
    if not path.exists():
        return []
    all_pdfs = [p for p in path.iterdir() if p.suffix == '.pdf']
    return sorted(_paths_to_pages(all_pdfs))


def _edition_subdirectory(date, subdir_template):
    """Return path to subdirectory of edition specified in the template"""
    ed_dir = edition_dir(date)
    return ed_dir.joinpath(subdir_template.format(date))


def edition_press_pdfs(date):
    """List pre-press PDFs for date's edition"""
    pdfs_dir = _edition_subdirectory(date, PRESS_PDFS_TEMPLATE)
    return directory_pdfs(pdfs_dir)


def edition_web_pdfs(date):
    """List low-quality PDFs for date's edition"""
    pdfs_dir = _edition_subdirectory(date, WEB_PDFS_TEMPLATE)
    return directory_pdfs(pdfs_dir)
