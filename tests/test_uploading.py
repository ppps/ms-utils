import msutils
import unittest
import unittest.mock as mock


class TestFTP(unittest.TestCase):
    """Test the send_pages_ftp function
    
    Its signature should match:
        send_pages_ftp(
            pages: [Page],
            host: str,
            user: str,
            passwd: str = '',
            path: str = None,
            rename: bool = True
            )
    
    It should iterate over the pages and upload them to the
    FTP server, saving to the correct subdirectory (path) and
    renaming (to the external format) as required.
    """
    def setUp(self):
        m = mock.Mock()
        m.external_name.return_value = 'Renamed'
        self.mock_pages = [m]
        self.ftp_args = dict(host='host', user='user', passwd='passwd')
        self.path = 'sub/dir'
    
    @mock.patch.object(msutils.ftplib.FTP, autospec=True)
    def test_FTP_setup(self, mock_FTP):
        """FTP constructor should be called with correct args"""
        msutils.send_pages_ftp(
                pages=self.mock_pages,
                **self.ftp_args
                )
        mock_FTP.assert_called_with(args)

    @mock.patch.object(msutils.ftplib.FTP, autospec=True)
    def test_FTP_right_directory(self, mock_FTP):
        """If path is supplied FTP.cwd should be called"""
        msutils.send_pages_ftp(
            pages=self.mock_pages,
            path=self.path,
            **self.ftp_args
            )
        mock_FTP.cwd.assert_called_with(self.path)
    
    @mock.patch.object(msutils.open, autospec=True)
    @mock.patch.object(msutils.ftplib.FTP, autospec=True)
    def test_FTP_stor_no_rename(self, mock_FTP, mock_open):
        """STOR commands correctly sent to the server, file not renamed"""
        open_retval = mock.Mock()
        mock_open.return_value = open_retval
        msutils.send_pages_ftp(
            pages=self.mock_pages,
            rename=False,
            **self.ftp_args
            )
            
        page_str = str(self.mock_pages[0])
        mock_open.assert_called_once()
        mock_open.assert_called_with(str(self.mock_pages[0]), 'b')
        mock_FTP.storbinary.assert_called_once()
        mock.FTP.storbinary.assert_called_with(
                f'STOR { page_str }', open_retval)

    @mock.patch.object(msutils.open, autospec=True)
    @mock.patch.object(msutils.ftplib.FTP, autospec=True)
    def test_FTP_stor_rename(self, mock_FTP, mock_open):
        """STOR commands correctly sent to the server, file not renamed"""
        open_retval = mock.Mock()
        mock_open.return_value = open_retval
        msutils.send_pages_ftp(
            pages=self.mock_pages,
            rename=True,
            **self.ftp_args
            )
            
        page_name = self.mock_pages.external_name()
        mock_open.assert_called_once()
        mock_open.assert_called_with(str(self.mock_pages[0]), 'b')
        mock_FTP.storbinary.assert_called_once()
        mock.FTP.storbinary.assert_called_with(
                f'STOR { page_name }', open_retval)


class TestSFTP(unittest.TestCase):
    pass

