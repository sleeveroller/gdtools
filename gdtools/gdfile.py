import logging
import os
import time
import sys

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

import hashlib

class GdFile:

  FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"

  def __init__(self, drive, simulate=False):
    """
    Create an instance of GdFile
    
    :param drive: a wrapper for google drive
    :type drive: pydrive.drive.GoogleDrive
    :param simulate: use simulation mode or not
    :type simulate: bool
    """
    self.drive = drive
    self.simulate = simulate
    self.logger = logging.getLogger('gdtools.GdFile')


  def create_directory(self, title, parent_id):
    """
    Create a new directory under the parent
    
    :param title: title of the new directory
    :type title: str
    :param parent_id: Google Drive id of the parent directory
    :type parent_id: str
    :returns: str - the Google Drive id of the new directory
    """

    new_id = None
    if self.simulate:
      new_id = 'SIMULATED_ID'
    else:
      f = self.drive.CreateFile({"title": title, "parents": [{"id": parent_id}],
                        "mimeType": self.FOLDER_MIME_TYPE})
      f.Upload()
      new_id = f['id']
    
    self.logger.info("created directory %s" % (title))
    return new_id


  def upload_file(self, local_path, title, parent_id):
    """
    upload a new file to google drive,
    if a file with the same name exists in the parent folder
    it won't be overwritten
    
    :param local_path: full path to the local file to be uploaded
    :type local_path: str
    :param title: the title to use for the file
    :type title: str
    :returns str -- the google drive id of the file
    """

    if self.simulate:
      return "SIMULATED_ID"

    f = self.drive.CreateFile({"title": title,
                "parents": [{"kind": "drive#childList", "id": parent_id}]})

    self._upload_file(f, local_path)
    
    if f['id']:
      return f['id']


  def update_file(self, local_path, gfile_id):
    """
    overwrite an existing file on google drive
    
    :param local_path: full path to the local file to be uploaded
    :type local_path: str
    :param gfile_id: a Google Drive File id
    :type gfile_id: str
    :returns: bool - True if the file was updated
    """
    f = self.drive.CreateFile({"id": gfile_id})
    if not self.is_identical(local_path, f['md5Checksum']):
      self.logger.info("local and remote files are different overwriting - %s" % (f['title']))
      if not self.simulate:
        self._upload_file(f, local_path)
      return True
    else:
      self.logger.info("local and remote files are the same - %s" % (f['title']))
    return False


  def _upload_file(self, gfile, local_path):
    """
    actually send the local file to Google Drive
    
    :param gfile: a Google Drive File instance
    :type gfile: pydrive.files.GoogleDriveFile
    :param local_path: full path to the local file to be uploaded
    :type local_path: str
    """
    
    self.logger.info("started uploading file %s" % (os.path.basename(local_path)))
    if not self.simulate:
      gfile.SetContentFile(local_path)
      gfile.Upload()
    self.logger.info("finished uploading file %s" % (os.path.basename(local_path)))


  def is_identical(self, local_path, gd_checksum):
    """
    check if the local file is different to the remote one

    :param local_path: full path to the local file
    :type local_path: str
    :param gd_checksum: md5Checksum from the Google Drive file
    :type gd_checksum: str
    :returns: bool - True if the checksums match
    """
    file_hash = self.md5_for_file(local_path, 8192, True)
    if file_hash == gd_checksum:
      return True
    else:
      return False


  def md5_for_file(self, path, block_size=256*128, hr=False):
    """
    Block size directly depends on the block size of your filesystem
    to avoid performances issues
    Here I have blocks of 4096 octets (Default NTFS)

    :param path: path to file to generate checksum for
    :type path: str
    :param block_size: block size to read in
    :type block_size: int
    :param hr: whether to return the checksum a hex string
    :type hr: bool
    :returns: str - the md5 checksum of the file
    """
    
    md5 = hashlib.md5()
    with open(path,'rb') as f: 
        for chunk in iter(lambda: f.read(block_size), b''): 
             md5.update(chunk)
    if hr:
        return md5.hexdigest()
    return md5.digest()


