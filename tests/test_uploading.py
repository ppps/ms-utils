import msutils.uploading
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
        m.path = '/Mock/Path.file'
        m.external_name.return_value = 'Renamed'
        self.mock_pages = [m]

        self.call_args = dict(host='host', user='user', password='password')
        self.ftp_args = self.call_args
        del self.ftp_args['password']
        self.ftp_args['passwd'] = 'password'

        self.path = 'sub/dir'

    @mock.patch.object(msutils.uploading.ftplib, 'FTP', autospec=True)
    def test_FTP_setup(self, mock_FTP):
        """FTP constructor should be called with correct args"""
        msutils.uploading.send_pages_ftp(
                pages=self.mock_pages,
                **self.call_args
                )
        mock_FTP.assert_called_with(self.ftp_args)

    @mock.patch.object(msutils.uploading.ftplib, 'FTP', autospec=True)
    def test_FTP_right_directory(self, mock_FTP):
        """If path is supplied FTP.cwd should be called"""
        msutils.uploading.send_pages_ftp(
            pages=self.mock_pages,
            path=self.path,
            **self.call_args
            )
        mock_FTP.cwd.assert_called_with(self.path)

    @mock.patch('builtins.open', autospec=True)
    @mock.patch.object(msutils.uploading.ftplib, 'FTP', autospec=True)
    def test_FTP_stor_no_rename(self, mock_FTP, mock_open):
        """STOR commands correctly sent to the server, file not renamed"""
        open_retval = mock.Mock()
        mock_open.return_value = open_retval
        msutils.uploading.send_pages_ftp(
            pages=self.mock_pages,
            rename=False,
            **self.call_args
            )

        mock_page = self.mock_pages[0]
        page_str = str(mock_page)
        mock_open.assert_called_once()
        mock_open.assert_called_with(mock_page.path, 'b')
        mock_FTP.storbinary.assert_called_once()
        mock.FTP.storbinary.assert_called_with(
                f'STOR { page_str }', open_retval)

    @mock.patch('builtins.open', autospec=True)
    @mock.patch.object(msutils.uploading.ftplib, 'FTP', autospec=True)
    def test_FTP_stor_rename(self, mock_FTP, mock_open):
        """STOR commands correctly sent to the server, file not renamed"""
        open_retval = mock.Mock()
        mock_open.return_value = open_retval
        msutils.uploading.send_pages_ftp(
            pages=self.mock_pages,
            rename=True,
            **self.call_args
            )

        mock_page = self.mock_pages[0]
        page_name = mock_page.external_name()
        mock_open.assert_called_once()
        mock_open.assert_called_with(mock_page.path, 'b')
        mock_FTP.storbinary.assert_called_once()
        mock.FTP.storbinary.assert_called_with(
                f'STOR { page_name }', open_retval)


class TestSFTP(unittest.TestCase):
    """Test the SFTP uploading function send_pages_sftp

    Its signature should match:
        send_pages_sftp(
            pages: [Page],
            host: str,
            port: int = 22,
            user: str,
            password: str = None
            path: str = None,
            rename: bool = True
            )

    It should iterate over the pages and upload them to
    the SFTP server, renaming them if specified, to the
    root or to the specified subdirectory (path).

    It should load keys from the system so that passwords
    are not required.
    """
    def setUp(self):
        m = mock.Mock()
        m.path = '/Mock/Path.file'
        m.external_name.return_value = 'Renamed'
        self.mock_pages = [m]

        self.call_args = dict(host='host', user='user',
                              password='password', port=526)
        self.sftp_args = dict(hostname='host', username='user',
                              password='password', port=526)

        self.path = 'sub/dir'

    @mock.patch.object(msutils.uploading.paramiko, 'SSHClient', autospec=True)
    def test_SFTP_called_with_args(self, mock_ssh):
        """Connection attempted with passed in arguments"""
        msutils.uploading.send_pages_sftp(
            pages=self.mock_pages,
            **self.call_args)
        mock_ssh.assert_called_once()
        mock_ssh.connect.assert_called_with(**self.sftp_args)

    @mock.patch.object(msutils.uploading.paramiko, 'SSHClient', autospec=True)
    def test_SFTP_right_directory(self, mock_ssh):
        """SFTP directory is changed after connection"""
        sftp = mock.Mock(spec=msutils.uploading.paramiko.SFTPClient)
        mock_ssh.open_sftp.return_value = sftp
        msutils.uploading.send_pages_sftp(
            pages=self.mock_pages,
            path=self.path,
            **self.call_args)
        sftp.chdir.assert_called_with(self.path)

    @mock.patch.object(msutils.uploading.paramiko, 'SSHClient', autospec=True)
    def test_SFTP_put_no_rename(self, mock_ssh):
        """SFTP puts local files without renaming"""
        sftp = mock.Mock(spec=msutils.uploading.paramiko.SFTPClient)
        mock_ssh.open_sftp.return_value = sftp
        msutils.uploading.send_pages_sftp(
            pages=self.mock_pages,
            path=self.path,
            rename=False,
            **self.call_args)
        sftp.put.assert_called_with(
            self.mock_pages[0].path,
            str(self.mock_pages[0]))

    @mock.patch.object(msutils.uploading.paramiko, 'SSHClient', autospec=True)
    def test_SFTP_put_renamed(self, mock_ssh):
        """SFTP puts local files and renames them"""
        sftp = mock.Mock(spec=msutils.uploading.paramiko.SFTPClient)
        mock_ssh.open_sftp.return_value = sftp
        msutils.uploading.send_pages_sftp(
            pages=self.mock_pages,
            path=self.path,
            rename=True,
            **self.call_args)
        sftp.put.assert_called_with(
            self.mock_pages[0].path,
            self.mock_pages[0].external_name())

