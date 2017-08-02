import msutils

import unittest
import unittest.mock as mock

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
		d = msutils.edition_dir(self.no_edition)
		self.assertIsInstance(d, pathlib.Path)

	def test_returns_path(self):
		"""edition_dir uses expected path format
		
		Edition dirs are found at:
			/Users/admin/Server/Pages/%Y-%m-%d %A %b %-d
		ie:
			/…/2017-08-02 Wednesday Aug 2
		
		In this test we stub out exists so that we get the Path
		returned and can check if it matches our expectations.
		"""
		# Mock out the .exists method so (hopefully) we don't get an exception
		msutils.pathlib.Path.exists = mock.Mock(return_value=True)
		d = msutils.edition_dir(self.no_edition)
		expected = '/Users/admin/Server/Pages/1929-12-31 Tuesday Dec 31'
		self.assertEqual(str(d), expected)

	def test_raises(self):
		"""edition_dir raises NoEditionError when it can't find the directory"""
		with self.assertRaises(msutils.NoEditionError):
			msutils.edition_dir(self.no_edition)
	
	