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
    with ftplib.FTP(host=host, user=user, passwd=password) as server:
        if path is not None:
            server.cwd(path)
        for page in pages:
            if rename:
                new_name = page.external_name()
            else:
                new_name = page.path.name
            with open(page.path, 'rb') as page_file:
                print(server.storbinary)
                server.storbinary(
                    f'STOR {new_name}',
                    page_file)


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
    try:
        ssh_client.connect(hostname=host, port=port, username=user,
                           password=password)
    except paramiko.AuthenticationException as e:
        print('Authentication failed:', e)
        return
    except paramiko.BadHostKeyException as e:
        print('Host key error:', e)
        return
    except paramiko.SSHException as e:
        print('SSH error prevented connection:', e)
        return

    with ssh_client.open_sftp() as server:
        if path is not None:
            server.chdir(path)
        for page in pages:
            if rename:
                new_name = page.external_name()
            else:
                new_name = page.path.name
            server.put(page.path, new_name)

    ssh_client.close()
