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
	def setUp(self):
		self.no_edition = datetime(1929, 12, 31)
	
	def test_returns_path(self):
		"""edition_dir returns a Path object"""
		# Mock out the .exists method so (hopefully) we don't get an exception
		msutils.pathlib.Path.exists = mock.Mock(return_value=True)
		ed = msutils.edition_dir(self.no_edition)
		self.assertIsInstance(ed, pathlib.Path)

	@given(st.datetimes())
	def test_expected_format(self, dt):
		"""edition_dir uses expected path format
		
		Edition dirs are found at:
			/Users/admin/Server/Pages/%Y-%m-%d %A %b %-d
		ie:
			/…/2017-08-02 Wednesday Aug 2
		
		In this test we stub out exists so that we get the Path
		returned and can check if it matches our expectations.
		
		Hypothesis is used to generate datetimes
		"""
		# Mock out the .exists method so (hopefully) we don't get an exception
		msutils.pathlib.Path.exists = mock.Mock(return_value=True)
		ed = msutils.edition_dir(self.no_edition)
		expected = f'/Users/admin/Server/Pages/{dt:%Y-%m-%d %A %b %-d}'
		self.assertEqual(str(ed), expected)

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
		
	def test_indd_files_extensions(self):
		"""Test Page types for edition_indd_files
		
		All the Pages returned by the function should have a .type of 'indd'
		"""
		msutils.pathlib.Path.exists = mock.Mock(return_value=True)
		msutils.pathlib.Path.iterdir = mock.Mock(
			return_value=(x for x in self.indd_names))
		res = msutils.edition_indd_files(self.no_edition)
		self.assertEqual({p.type for p in res}, {'indd'})
		
	def test_pdf_files_extensions(self):
		"""Test Page types for edition_press_pdfs and edition_web_pdfs
		
		All the Pages returned by the function should have a .type of 'pdf'
		"""
		msutils.pathlib.Path.exists = mock.Mock(return_value=True)
		msutils.pathlib.Path.iterdir = mock.Mock(
			return_value=(x for x in self.pdf_names))
		res = msutils.edition_press_pdfs(self.no_edition)
		res.extend(msutils.edition_web_pdfs(self.no_edition))
		self.assertEqual({p.type for p in res}, {'pdf'})
