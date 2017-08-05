from pathlib import Path

from .page import Page

PAGES_ROOT = Path('~/Server/Pages/').expanduser()
PAGES_TEMPLATE = '{0:%Y-%m-%d %A %b %-d}'
PDFS_TEMPLATE = '{0:PDFs %d%m%y}'
WEB_PDFS_TEMPLATE = '{0:E-edition PDFs %d%m%y}'


class NoEditionError(Exception):
    """No edition can be found for the given date"""
    pass


def edition_dir(date):
    """Return path to date's edition directory

    Raises NoEditionError if an edition can't be
    found in the expected locations for date.
    """
    ed_dir = PAGES_ROOT.joinpath(
        PAGES_TEMPLATE.format(date)
        )
    if ed_dir.exists():
        return ed_dir.resolve()
    else:
        raise NoEditionError(f'Cannot find edition for {date:%Y-%m-%d}')


def _edition_press_pdfs_dir(date):
    """Return path to pre-press PDFs directory for date's edition"""
    ed_dir = edition_dir(date)
    return ed_dir.joinpath(PDFS_TEMPLATE.format(date))


def _edition_web_pdfs_dir(date):
    """Return path to pre-press PDFs directory for date's edition"""
    ed_dir = edition_dir(date)
    return ed_dir.joinpath(WEB_PDFS_TEMPLATE.format(date))


def _paths_to_pages(paths):
    """Yield Pages from Paths, handling exceptions from non-Pages"""
    for p in paths:
        try:
            yield Page(p)
        except ValueError:
            continue


def _parse_pdfs_dir(path):
    """List Page-acceptable PDFs in path"""
    # PDFs directory may not exist yet, even if the edition does
    if not path.exists():
        return []
    all_pdfs = [p for p in path.iterdir() if p.suffix == '.pdf']
    return sorted(_paths_to_pages(all_pdfs))


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


def edition_press_pdfs(date):
    """List pre-press PDFs for date's edition"""
    pdfs_dir = _edition_press_pdfs_dir(date)
    return _parse_pdfs_dir(pdfs_dir)


def edition_web_pdfs(date):
    """List low-quality PDFs for date's edition"""
    pdfs_dir = _edition_web_pdfs_dir(date)
    return _parse_pdfs_dir(pdfs_dir)
