import logging
import os
import time
import sys

from Queue import Queue

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from gdfind import GdFind
from gdfile import GdFile


class GdSync:

  def __init__(self, upload_queue, drive, local_path, remote_path=os.path.sep, overwrite=False, simulate=False):
    """
    Create an instance of GdSync
    
    :param upload_queue: queue for uploading files asynchronously
    :type upload_queue: Queue.Queue
    :param drive: a wrapper for google drive
    :type drive: pydrive.drive.GoogleDrive
    :param local_path: local directory to use as the root
    :type local_path: str
    :param remote_path: Path on Google Drive to upload to e.g. /photos
    :type remote_path: str
    :param overwrite: whether to overwrite files that already exist during sync
    :type overwrite: bool
    :param simulate: use simulation mode or not
    :type simulate: bool
    """
    self.upload_queue = upload_queue
    self.drive = drive
    self.local_path = local_path
    self.local_name = os.path.basename(os.path.normpath(local_path))
    self.remote_path = remote_path
    self.overwrite = overwrite
    self.finder = GdFind(drive)
    self.simulate = simulate
    self.files = GdFile(drive, simulate)
    self.logger = logging.getLogger('gdtools.GdSync')


  def push(self):
    """
    Recursively loop through the directory, and upload items
    """
    
    parent_id = self.finder.find_file_from_remote_path(self.remote_path)
    name = self.local_name
    is_file = os.path.isfile(self.local_path)   
    remote_path = self.finder.find_file_from_title(name, parent_id)
    if is_file:
      if remote_path and remote_path['mimeType'] == self.files.FOLDER_MIME_TYPE:
        self.logger.error("%s is a remote directory" % name)
      elif remote_path and self.overwrite:
        self.upload_queue.put((self.local_path, name, remote_path, True,))
        self.logger.debug("added %s to the upload queue for overwriting" % (name))
      elif not remote_path:
        self.upload_queue.put((self.local_path, name, parent_id, False))
        self.logger.debug("added %s to the upload queue" % (name))
      else:
        self.logger.error("%s already exists use overwrite to force upload" % name)
      return

    if remote_path and remote_path['mimeType'] != self.files.FOLDER_MIME_TYPE:
      self.logger.error("%s exists but is not a directory" % name)
      return

    is_new = False
    if remote_path:
      dir_id = remote_path['id']
    else:
      dir_id = self.files.create_directory(name, parent_id)
      is_new = True
      
    self._push(self.local_path, dir_id, is_new)


  def _push(self, local_dir, dir_id, dir_is_new):
    """
    Recursively loop through the directory,
    upload items missing from Google Drive
    
    :param local_dir: local directory to push
    :type local_dir: str
    :param dir_id: Google Drive id of the directory to check against
    :type dir_id: str
    :param dir_is_new: True if the local directory is new Google Drive
    :type dir_is_new: bool
    """
    
    if not dir_is_new:
      remote_file_list = self.finder.list_files(dir_id)
    else:
      remote_file_list = None

    for item in sorted(os.listdir(local_dir)):

      gd_id = None
      local_path = os.path.join(local_dir, item)
      is_file = os.path.isfile(local_path)

      if not dir_is_new:
        self.logger.info("scanning %s" % (local_path))

        gfiles = [x for x in remote_file_list if x['title'] == item]
        if gfiles:
          gd_id = gfiles[0]['id']

      gd_id_is_new = False
      if gd_id is None:
        if not is_file:
          gd_id = self.files.create_directory(item, dir_id)
          gd_id_is_new = True
        else:
          self.upload_queue.put((local_path, item, dir_id, False,))
          self.logger.debug("added %s to the upload queue" % (item))
      elif is_file and self.overwrite:
        self.upload_queue.put((local_path, item, gd_id, True,))
        self.logger.debug("added %s to the upload queue for update" % (item))

      if gd_id and not is_file:
        self._push(local_path, gd_id, gd_id_is_new)



