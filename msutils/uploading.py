import ftplib
import logging

import paramiko

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


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
    try:
        with ftplib.FTP(host=host, user=user, passwd=password) as server:
            logger.debug('Connected to %s as %s', host, user)
            if path is not None:
                server.cwd(path)
                logger.debug('Changed to directory %s', path)
            for page in pages:
                if rename:
                    new_name = page.external_name()
                else:
                    new_name = page.path.name
                with open(page.path, 'rb') as page_file:
                    logger.debug('Opened %s for uploading', page.path)
                    server.storbinary(
                        f'STOR {new_name}',
                        page_file)
                    logger.info('Uploaded file: %s    ->    %s',
                                page, new_name)
    except ftplib.all_errors as e:
        logger.error('FTP uploading encountered an error: %s', e)


def send_pages_sftp(pages, host, user, password=None,
                    port=22, path=None, rename=True):
    """Upload a set of Pages to an SFTP server

    pages: [Page],
    host: str,
    user: str,
    password: str = None,
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
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    if password is None:
        ssh_client.load_system_host_keys()
        logger.debug('Loaded system SSH keys')
    try:
        ssh_client.connect(hostname=host, port=port, username=user,
                           password=password)
    except paramiko.AuthenticationException as e:
        logger.error('Could not connect to %s as %s'
                     'because of an authentication error',
                     host, user)
        logger.error('Error: %s', e)
        return
    except paramiko.BadHostKeyException as e:
        logger.error('Could not connect to %s as %s'
                     'because of an SSH key error',
                     host, user)
        logger.error('Error: %s', e)
        return
    except paramiko.SSHException as e:
        logger.error('Could not connect to %s as %s'
                     'because of an SSH problem',
                     host, user)
        logger.error('Error: %s', e)
        return
    else:
        logger.debug('Connected to %s as %s', host, user)

    with ssh_client.open_sftp() as server:
        if path is not None:
            server.chdir(path)
            logger.debug('Changed to directory %s', path)
        for page in pages:
            if rename:
                new_name = page.external_name()
            else:
                new_name = page.path.name
            server.put(page.path, new_name)
            logger.info('Uploaded file: %s    ->    %s', page, new_name)

    ssh_client.close()
