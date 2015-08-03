import logging
import os
import time

from pydrive.drive import GoogleDrive

class GdFind:

  MAX_RETRIES = 3

  GD_ROOT_ID = 'root'

  def __init__(self, drive):
    """
    Create an instance of GdFind
    
    :param drive: a wrapper for google drive
    :type drive: pydrive.drive.GoogleDrive
    """
    self.drive = drive
    self.logger = logging.getLogger('gdtools.GdFind')


  def find_file_from_remote_path(self, remote_path):

    if remote_path == os.path.sep:
      return self.GD_ROOT_ID

    names = remote_path.split(os.path.sep)
    parent_id = self.GD_ROOT_ID

    for name in names:
      if name != '':
        self.logger.info(name)
        f = self.find_file_from_title(name, parent_id)
        if f:
          parent_id = f['id']
        else:
          raise Exception

    return parent_id


  def find_file_from_title(self, title, parent_id):
    """
    Get a single id from google drive
    
    :param title: title of the file in Google Drive
    :type title: str
    :param parent_id: Google Drive Id of the parent directory
    :type parent_id: str
    :returns: pydrive.files.GoogleDriveFile
    """

    query = "'%s' in parents and trashed=false and title='%s'" % (parent_id, title)
    file_list = self._list_files(query)
    if file_list:
      return file_list[0]
    return None


  def list_files(self, parent_id):
    """
    List contents of directory
    
    :param parent_id: Google Drive Id of the parent directory
    :type parent_id: str
    :returns: list of pydrive.files.GoogleDriveFile instances
    """

    query = "'%s' in parents and trashed=false" % (parent_id)
    return self._list_files(query)


  def _list_files(self, query):
    """
    Get a list of files based on a query
    
    :param query: Search query for Google Drive
    :type query: str
    :returns: list of pydrive.files.GoogleDriveFile instances
    """

    count = 0
    while count < self.MAX_RETRIES:
      try:
        file_list = self.drive.ListFile({'q': query}).GetList()
        return file_list
      except:
        count = count + 1
        self.logger.warning("listing files attempt %d of %d (query: %s)" %
                               (count, self.MAX_RETRIES, query))
        time.sleep(1)
    raise



