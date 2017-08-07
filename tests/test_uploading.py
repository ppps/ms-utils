import msutils.uploading
from pathlib import Path
import unittest
import unittest.mock as mock

import paramiko


class TestFTP(unittest.TestCase):
    """Test the send_pages_ftp function

    Its signature should match:
        send_pages_ftp(
            pages: [Page],
            host: str,
            user: str,
            password: str = '',
            path: str = None,
            rename: bool = True
            )

    It should iterate over the pages and upload them to the
    FTP server, saving to the correct subdirectory (path) and
    renaming (to the external format) as required.
    """
    def setUp(self):
        m = mock.Mock()
        m.path = Path('/Mock/Path.file')
        m.external_name.return_value = 'Renamed'
        self.mock_pages = [m]

        self.call_args = dict(host='host', user='user', password='password')
        self.ftp_args = self.call_args.copy()
        del self.ftp_args['password']
        self.ftp_args['passwd'] = 'password'

        self.path = 'sub/dir'

    @mock.patch('builtins.open', autospec=True)
    @mock.patch.object(msutils.uploading.ftplib, 'FTP', autospec=True)
    def test_FTP_setup(self, mock_FTP, mock_open):
        """FTP constructor should be called with correct args"""
        msutils.uploading.send_pages_ftp(
                pages=self.mock_pages,
                **self.call_args
                )
        mock_FTP.assert_called_with(**self.ftp_args)

    @mock.patch('builtins.open', autospec=True)
    @mock.patch.object(msutils.uploading.ftplib, 'FTP', autospec=True)
    def test_FTP_right_directory(self, mock_FTP, mock_open):
        """If path is supplied FTP.cwd should be called"""
        ftp_cm = mock_FTP.return_value.__enter__.return_value
        msutils.uploading.send_pages_ftp(
            pages=self.mock_pages,
            path=self.path,
            **self.call_args
            )
        ftp_cm.cwd.assert_called_with(self.path)

    @mock.patch('builtins.open', autospec=True)
    @mock.patch.object(msutils.uploading.ftplib, 'FTP', autospec=True)
    def test_FTP_stor_no_rename(self, mock_FTP, mock_open):
        """STOR commands correctly sent to the server, file not renamed"""
        ftp_cm = mock_FTP.return_value.__enter__.return_value
        open_cm = mock_open.return_value.__enter__.return_value
        msutils.uploading.send_pages_ftp(
            pages=self.mock_pages,
            rename=False,
            **self.call_args
            )

        mock_path = self.mock_pages[0].path
        mock_open.assert_called_once()
        mock_open.assert_called_with(mock_path, 'rb')
        ftp_cm.storbinary.assert_called_once()
        ftp_cm.storbinary.assert_called_with(
                f'STOR { mock_path.name }', open_cm)

    @mock.patch('builtins.open', autospec=True)
    @mock.patch.object(msutils.uploading.ftplib, 'FTP', autospec=True)
    def test_FTP_stor_rename(self, mock_FTP, mock_open):
        """STOR commands correctly sent to the server, file not renamed"""
        ftp_cm = mock_FTP.return_value.__enter__.return_value
        open_cm = mock_open.return_value.__enter__.return_value
        msutils.uploading.send_pages_ftp(
            pages=self.mock_pages,
            rename=True,
            **self.call_args
            )

        mock_page = self.mock_pages[0]
        page_name = mock_page.external_name()
        mock_open.assert_called_once()
        mock_open.assert_called_with(mock_page.path, 'rb')
        ftp_cm.storbinary.assert_called_once()
        ftp_cm.storbinary.assert_called_with(
                f'STOR { page_name }', open_cm)


class TestSFTP(unittest.TestCase):
    """Test the SFTP uploading function send_pages_sftp

    Its signature should match:
        send_pages_sftp(
            pages: [Page],
            host: str,
            user: str,
            password: str = None,
            port: int = 22,
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
        m.path = Path('/Mock/Path.file')
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
        client = mock_ssh.return_value
        msutils.uploading.send_pages_sftp(
            pages=self.mock_pages,
            **self.call_args)
        mock_ssh.assert_called_once()
        client.connect.assert_called_with(**self.sftp_args)

    @mock.patch.object(msutils.uploading.paramiko, 'SSHClient', autospec=True)
    def test_SFTP_loads_keys_with_no_password(self, mock_ssh):
        """Test loading of SSH keys when no password is supplied"""
        client = mock_ssh.return_value
        args = self.call_args.copy()
        args['password'] = None
        msutils.uploading.send_pages_sftp(
            pages=self.mock_pages,
            **args)
        client.load_system_host_keys.assert_called()

    @mock.patch.object(msutils.uploading.paramiko, 'SSHClient', autospec=True)
    def test_SFTP_right_directory(self, mock_ssh):
        """SFTP directory is changed after connection"""
        sftp = mock.Mock(spec=msutils.uploading.paramiko.SFTPClient)
        ssh_client = mock_ssh.return_value
        ssh_client.open_sftp.return_value.__enter__.return_value = sftp
        msutils.uploading.send_pages_sftp(
            pages=self.mock_pages,
            path=self.path,
            **self.call_args)
        sftp.chdir.assert_called_with(self.path)

    @mock.patch.object(msutils.uploading.paramiko, 'SSHClient', autospec=True)
    def test_SFTP_put_no_rename(self, mock_ssh):
        """SFTP puts local files without renaming"""
        sftp = mock.Mock(spec=msutils.uploading.paramiko.SFTPClient)
        ssh_client = mock_ssh.return_value
        ssh_client.open_sftp.return_value.__enter__.return_value = sftp
        msutils.uploading.send_pages_sftp(
            pages=self.mock_pages,
            path=self.path,
            rename=False,
            **self.call_args)
        sftp.put.assert_called_with(
            self.mock_pages[0].path,
            self.mock_pages[0].path.name)

    @mock.patch.object(msutils.uploading.paramiko, 'SSHClient', autospec=True)
    def test_SFTP_put_renamed(self, mock_ssh):
        """SFTP puts local files and renames them"""
        sftp = mock.Mock(spec=msutils.uploading.paramiko.SFTPClient)
        ssh_client = mock_ssh.return_value
        ssh_client.open_sftp.return_value.__enter__.return_value = sftp
        msutils.uploading.send_pages_sftp(
            pages=self.mock_pages,
            path=self.path,
            rename=True,
            **self.call_args)
        sftp.put.assert_called_with(
            self.mock_pages[0].path,
            self.mock_pages[0].external_name())

    @mock.patch.object(msutils.uploading.paramiko, 'SSHClient', autospec=True)
    def test_SFTP_handle_connection_exceptions(self, mock_ssh):
        """SFTP should catch exceptions raised when trying to connect"""
        # Before you implement the logging you'll want to test for it here
        exceptions = [
            paramiko.AuthenticationException,
            paramiko.BadHostKeyException(
                mock.Mock(), mock.Mock(), mock.Mock()),
            paramiko.SSHException]
        mock_ssh.return_value.connect.side_effect = exceptions
        for exc in exceptions:
            with self.subTest(msg=str(exc)):
                try:
                    msutils.uploading.send_pages_sftp(
                        pages=self.mock_pages,
                        **self.call_args)
                except Exception as e:
                    self.fail(str(e))
