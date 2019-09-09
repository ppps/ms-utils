import msutils
import msutils.edition

import unittest
import unittest.mock as mock

from hypothesis import given, assume
import hypothesis.strategies as st

from datetime import date
import pathlib


class TestEditionDir(unittest.TestCase):
    """Test the .edition_dir function

    It should take a date and return a pathlib.Path object corresponding to
    the edition for that day.

    If there is no such edition it should raise a msutils.NoEditionError.
    """
    edition_stores = [
        pathlib.Path(p).expanduser() for p in
        ['~/Server/Pages',
         '/Volumes/MS-T4-Archive-2002-2016',
         '/Volumes/MS-T4-Archive-Since-2017',
         '/Volumes/Server/Pages',
         '/Volumes/Archive 2002-2016',
         '/Volumes/Archive since 2017']]
    archive_stores = [edition_stores[1], edition_stores[2],
                      edition_stores[4], edition_stores[5]]

    @given(dt=st.dates())
    @mock.patch.object(msutils.edition.Path, 'exists', return_value=True)
    def test_returns_path(self, mock_exists, dt):
        """edition_dir returns a Path object"""
        ed = msutils.edition_dir(dt)
        self.assertIsInstance(ed, pathlib.Path)

    @mock.patch.object(msutils.edition.Path, 'exists', return_value=False)
    def test_fetch_stores_raises(self, mock_exists):
        """_fetch_stores raises when none of the edition stores exist

        _fetch_stores should return a list of all the edition stores that
        exist on the current machine. If none of them exist it should raise
        a NoEditionStoresError.
        """
        with self.assertRaises(msutils.NoEditionStoresError):
            msutils.edition._fetch_stores()

    @given(bools=st.lists(elements=st.booleans(), min_size=6, max_size=6))
    @mock.patch.object(msutils.edition.Path, 'exists', autospec=True)
    def test_fetch_stores_matching_bools(self, mock_exists, bools):
        """_fetch_stores returns paths for which mock_exist returns True

        The paths are known quantities:
            * ~/Server/Pages                        # Local Pages
            * /Volumes/MS-T4-Archive-2002-2016      # Local old archive
            * /Volumes/MS-T4-Archive-Since-2017     # Local new archive
            * /Volumes/Server/Pages                 # Remote Pages
            * /Volumes/Archive-2002-2016            # Remote old archive
            * /Volumes/Archive-Since-2017           # Remote new archive

        These are zipped with a list of booleans — those zipped with True
        should be present in the output list.
        """
        assume(any(bools))  # All False would raise an error, tested separately
        paths_exist = dict(zip(self.edition_stores, bools))
        mock_exists.side_effect = lambda path: paths_exist[path]

        # Only test the paths, not the templates _fetch_stores returns
        self.assertEqual(
            sorted(p for (p, t) in msutils.edition._fetch_stores()),
            sorted(p for p in paths_exist if paths_exist[p]))

    @given(picked_path=st.sampled_from(edition_stores))
    @mock.patch.object(msutils.edition.Path, 'exists', autospec=True)
    def test_edition_dir_tests_all(self, mock_exists, picked_path):
        """edition_dir should return path when it is found in any store

        Here we mock out exists and return True for one of the six edition
        stores. We also return True for any directory that is a subdirectory
        (at any level) of the picked edition store path.

        Using Hypothesis lets us check that this works for any of the
        edition stores, and not just a single (perhaps hard-coded) one.
        """
        def exists_faker(path):
            return str(path).startswith(str(picked_path))
        mock_exists.side_effect = exists_faker
        assert msutils.edition_dir(date(2010, 9, 20))

    @given(
        dt=st.dates(),
        picked_path=st.sampled_from([edition_stores[0], edition_stores[3]]))
    @mock.patch.object(msutils.edition.Path, 'exists', autospec=True)
    def test_expected_format_for_current(self, mock_exists, picked_path, dt):
        """edition_dir uses expected path format for 'current' editions

        Current edition dirs are found at:
                (~|/Volumes)/Server/Pages/%Y-%m-%d %A %b %-d
        ie:
                /…/2017-08-02 Wednesday Aug 2

        In this test we stub out exists so that we get the Path
        returned and can check if it matches our expectations.

        Hypothesis is used to generate dates
        """
        def exists_faker(path):
            return str(path).startswith(str(picked_path))
        mock_exists.side_effect = exists_faker

        ed = msutils.edition_dir(dt)
        expected_pattern = f'/Server/Pages/{dt:%Y-%m-%d %A %b %-d}'
        assert str(ed).endswith(expected_pattern)

    @given(dt=st.dates(), picked_path=st.sampled_from(archive_stores))
    @mock.patch.object(msutils.edition.Path, 'exists', autospec=True)
    def test_expected_format_for_archive(self, mock_exists, picked_path, dt):
        """edition_dir uses expected path format for 'archive' editions

        Archive edition dirs are found at:
                ARCHIVE_DIR/%Y/%m %B/%Y-%m-%d %A/
        ie:
                ARCHIVE_DIR/2017/08 August/2017-08-02 Wednesday

        Where ARCHIVE_DIR is one of:
            * /Volumes/MS-T4-Archive-2002-2016',
            * /Volumes/MS-T4-Archive-Since-2017',
            * /Volumes/Archive-2002-2016',
            * /Volumes/Archive-Since-2017']]

        In this test we stub out exists so that we get the Path
        returned and can check if it matches our expectations.

        Hypothesis is used to generate dates
        """
        def exists_faker(path):
            return str(path).startswith(str(picked_path))
        mock_exists.side_effect = exists_faker

        ed = msutils.edition_dir(dt)
        expected_pattern = f'/{dt:%Y}/{dt:%m %B}/{dt:%Y-%m-%d %A}'
        assert str(ed).endswith(expected_pattern)

    @given(dt=st.one_of(
            st.dates(max_date=date(2001, 12, 31)),
            st.dates(min_date=date(2030, 1, 1))))
    @mock.patch.object(msutils.edition.Path, 'exists', autospec=True)
    def test_raises_no_edition(self, mock_exists, dt):
        """edition_dir raises NoEditionError when it can't find the directory

        Mocking ensures that the edition stores are available, so this
        tests the raising behaviour when just the edition is missing.

        Hypothesis is used to generate a date (< 2002 | > 2029).

        (God forbid you're still running these tests in 2030.)
        """
        def exists_faker(path):
            return path in self.edition_stores
        mock_exists.side_effect = exists_faker
        with self.assertRaises(msutils.NoEditionError):
            msutils.edition_dir(dt)


class TestEditionFiles(unittest.TestCase):
    """Test the functions which fetch lists of edition files

    edition_indd_files
    edition_press_pdfs
    edition_web_pdfs
    """
    def setUp(self):
        self.no_edition = date(2000, 1, 2)
        names = [f'{i}_Section_020100.' for i in range(1, 17)]
        self.indd_names = [pathlib.Path(n + 'indd') for n in names]
        self.pdf_names = [pathlib.Path(n + 'pdf') for n in names]

    @mock.patch('msutils.edition', 'os.walk')
    @mock.patch.object(msutils.edition.Path, 'rglob')
    @mock.patch.object(msutils.edition.Path, 'exists', return_value=True)
    def test_indd_files_extensions(self, mock_exists,
                                   mock_rglob=None, mock_walk=None):
        """Test Page types for edition_indd_files

        Function should use either Path.rglob or os.walk to recursively
        find all InDesign files in the edition directory. This is done
        because supplements are often stored in a subdirectory of the
        edition, to avoid cluttering the edition listing.

        Both Path.rglob and os.walk are mocked out and it is acceptable
        to use either.

        All the Pages returned by the function should have a .type of 'indd'
        """
        indd_gen = (x for x in self.indd_names)

        # mock_rglob always needs a value because pathlib is always imported
        mock_rglob.return_value = indd_gen
        if mock_walk is not None:
            # os is only imported by edition if walk is needed
            mock_walk.side_effect = [
                ['', [], self.indd_list[:8]],
                ['', [], self.indd_list[8:]]]

        res = msutils.edition_indd_files(self.no_edition)
        self.assertEqual({p.type for p in res}, {'indd'})
        self.assertEqual(len(res), len(self.indd_names))

        if mock_walk is not None:
            mock_walk.assert_called()
        else:
            mock_rglob.assert_called()

    @mock.patch.object(msutils.edition.Path, 'exists', return_value=True)
    def test_pdf_files_extensions(self, mock_exists):
        """Test Page types for edition_press_pdfs and edition_web_pdfs

        All the Pages returned by the function should have a .type of 'pdf'
        """
        pdf_gen = (x for x in self.pdf_names)
        with mock.patch.object(msutils.edition.Path, 'iterdir',
                               return_value=pdf_gen):
            res = msutils.edition_press_pdfs(self.no_edition)
            res.extend(msutils.edition_web_pdfs(self.no_edition))
            self.assertEqual({p.type for p in res}, {'pdf'})

    @mock.patch.object(msutils.edition.Path, 'exists', return_value=False)
    def test_directory_pdfs_missing(self, mock_exists):
        """directory_pdfs returns an empty list if the directory does not exist

        This is acceptable rather than throwing an exception because the PDFs
        directories (both kinds) for an edition are created on demand when the
        PDFs themselves are created."""
        fake_path = pathlib.Path('no-directory-here')
        self.assertEqual(msutils.directory_pdfs(fake_path), [])

    @mock.patch.object(msutils.edition.Path, 'iterdir')
    @mock.patch.object(msutils.edition.Path, 'exists', return_value=True)
    def test_directory_pdfs_filter_nonpages(self, mock_exists, mock_iterdir):
        """directory_pdfs returns expected number of pages from directory"""
        mock_iterdir.return_value = [pathlib.Path('A1_TestPage_010217.pdf'),
                                     pathlib.Path('not-a-page.pdf')]
        res = msutils.directory_pdfs(pathlib.Path('dummy-dir'))
        self.assertEqual(len(res), 1)

    def test_filter_pages_for_date_all_same(self):
        """No pages filtered if date is what is expected."""
        pages = [msutils.Page(path) for path in self.pdf_names]
        self.assertEqual(
            pages,
            msutils.edition._filter_pages_for_date(pages, date=self.no_edition)
        )

    def test_filter_pages_for_date_filters_mixed_dates(self):
        """Only pages with matching date are returned"""
        same_date_pages = [msutils.Page(path) for path in self.pdf_names]
        mixed_date_pages = same_date_pages + [
            msutils.Page(pathlib.Path(f'1_Front_3107{year}.pdf')) for year in range(50, 60)
        ]
        self.assertEqual(
            same_date_pages,
            msutils.edition._filter_pages_for_date(mixed_date_pages, date=self.no_edition)
        )
