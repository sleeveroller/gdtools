import argparse
import logging
import logging.handlers
import sys

from sys import argv
from Queue import Queue, Empty
from threading import Thread

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from gdsync import GdSync
from gdfile import GdFile

_killed = False
_num_new_files = 0
_num_updated_files = 0

LOG_FILENAME = 'gdtools.log'

def file_uploader(q, simulate):

  global _num_new_files
  global _num_updated_files

  logger = logging.getLogger('gdtools')

  gauth = GoogleAuth()
  gauth.LocalWebserverAuth()

  drive_uploader = GoogleDrive(gauth)

  gdfu = GdFile(drive_uploader, simulate)

  while not _killed or not q.empty():

    try:
      logger.debug('checking upload queue')
      item = q.get(True, 5)
      try:
        logger.info("processing %s from the upload queue, queue size is now %d" % (item[1], q.qsize()))
        if item[3] == True:
          if gdfu.update_file(item[0], item[2]):
            _num_updated_files += 1
        else:
          gdfu.upload_file(item[0], item[1], item[2])
          _num_new_files += 1
      except Exception, e:
        logger.error(e)
      finally:
        q.task_done()

    except Empty:
      pass


def sync(args):

  global _killed

  logger = logging.getLogger('gdtools')

  logger.info(args)
  if args.simulate:
    logger.info('running in simuation mode, no changes will be made to local or remote file systems')
  
  gauth = GoogleAuth()
  gauth.LocalWebserverAuth()

  if gauth.access_token_expired:
    sys.exit(2)
    
  upload_queue = Queue()

  t = Thread(target = file_uploader, args = (upload_queue, args.simulate,))
  t.start()

  try:
    drive = GoogleDrive(gauth)

    gd = GdSync(upload_queue, drive, args.localPath,
                    args.remotePath, args.overwrite, args.simulate)
    gd.push()
    _killed = True
  
    logger.info("scanning done, waiting for uploads to finish")
    upload_queue.join()
    logger.info("finished, %d new file(s) uploaded, %d file(s) updated" % 
                    (_num_new_files, _num_updated_files))

  finally:
    _killed = True


def setup_logging():

  gdlogger = logging.getLogger('gdtools')
  gdlogger.setLevel(logging.DEBUG)

  handler = logging.handlers.RotatingFileHandler(
                LOG_FILENAME, maxBytes=10*1024*1024, backupCount=5)

  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  handler.setFormatter(formatter)
  gdlogger.addHandler(handler)

  ch = logging.StreamHandler()
  ch.setLevel(logging.INFO)

  chformatter = logging.Formatter('%(asctime)s - %(message)s')
  ch.setFormatter(chformatter)
  gdlogger.addHandler(ch)


if __name__ == '__main__':

  setup_logging()

  parser = argparse.ArgumentParser(prog='gdtools',
                    description='manage file syncing to google drive')

  parser.add_argument('mode', choices=['push','pull'], help='mode help')
  parser.add_argument('localPath', help='localPath help')
  parser.add_argument('remotePath', help='remotePath help')
  parser.add_argument('-s', '--simulate', action='store_true')
  parser.add_argument('-o', '--overwrite', action='store_true')
  parser.set_defaults(func=sync)

  args = parser.parse_args()
  args.func(args)



