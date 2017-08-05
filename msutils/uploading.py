import ftplib
import paramiko


def send_pages_ftp(pages, host, user, password='',
                   path=None, rename=True):
    """Upload a set of Pages to an FTP server

    pages: [Page],
    host: str,
    user: str,
    passwd: str = '',
    path: str = None,
    rename: bool = True

    Mostly a convenience wrapper around ftplib.FTP.

    If given, path refers to the subdirectory or chain of
    subdirectories into which the FTP client will change
    before attempting to upload any files.

    If rename is True (the default), each page will be renamed
    by calling its external_name method. If rename is False the
    page's current filename will be used.
    """
    pass


def send_pages_sftp(pages, host, user, password=None,
                    port=22, path=None, rename=True):
    """Upload a set of Pages to an SFTP server

    pages: [Page],
    host: str,
    user: str,
    passwd: str = None,
    port: int = 22,
    path: str = None,
    rename: bool = True

    Mostly a convenience wrapper around paramiko's classes.

    If password is None, private keys will be loaded from
    the system for authentication.

    If given, path refers to the subdirectory or chain of
    subdirectories into which the FTP client will change
    before attempting to upload any files.

    If rename is True (the default), each page will be renamed
    by calling its external_name method. If rename is False the
    page's current filename will be used.
    """
    pass
