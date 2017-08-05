import msutils

import unittest
import unittest.mock as mock

from hypothesis import given
import hypothesis.strategies as st

from datetime import datetime
import pathlib


class TestEditionDir(unittest.TestCase):
    """Test the .edition_dir function

    It should take a datetime and return a pathlib.Path object corresponding to
    the edition for that day.

    If there is no such edition it should raise a msutils.NoEditionError.
    """
    @given(dt=st.datetimes())
    @mock.patch.object(msutils.edition.Path, 'exists', return_value=True)
    def test_returns_path(self, mock_exists, dt):
        """edition_dir returns a Path object"""
        ed = msutils.edition_dir(dt)
        self.assertIsInstance(ed, pathlib.Path)

    @given(dt=st.datetimes())
    @mock.patch.object(msutils.edition.Path, 'exists', return_value=True)
    def test_expected_format(self, mock_exists, dt):
        """edition_dir uses expected path format

        Edition dirs are found on the server at:
                ~/Server/Pages/%Y-%m-%d %A %b %-d
        ie:
                /…/2017-08-02 Wednesday Aug 2

        In this test we stub out exists so that we get the Path
        returned and can check if it matches our expectations.

        Hypothesis is used to generate datetimes
        """
        ed = msutils.edition_dir(dt)
        expected = pathlib.Path(f'~/Server/Pages/{dt:%Y-%m-%d %A %b %-d}')
        expected = expected.expanduser()
        self.assertEqual(ed, expected)

    @given(st.one_of(
            st.datetimes(max_datetime=datetime(2002, 1, 1)),
            st.datetimes(min_datetime=datetime(2030, 1, 1))))
    def test_raises(self, dt):
        """edition_dir raises NoEditionError when it can't find the directory

        Hypothesis is used to generate a date (< 2002 | > 2029).

        (God forbid you're still running these tests in 2030.)
        """
        with self.assertRaises(msutils.NoEditionError):
            msutils.edition_dir(dt)


class TestEditionFiles(unittest.TestCase):
    """Test the functions which fetch lists of edition files

    edition_indd_files
    edition_press_pdfs
    edition_web_pdfs
    """
    def setUp(self):
        self.no_edition = datetime(1929, 12, 31)
        names = [f'{i}_Section_311229.' for i in range(1, 17)]
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
