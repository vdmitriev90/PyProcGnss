import datetime as dt
import ftplib 
import os, sys, os.path

import re
import shutil

import FtpDownload as dld

class DownloadBCE(dld.DownloadBase):
      """download broadcast ephemeris from CDDIS FTP"""          
      def __init__(self,SsLitera):
          """Constructor"""
          dld.DownloadBase.__init__(self, 'NAV')
          self.SsLitera = SsLitera 

      def _download(self, t1, t2, workingDir):
          """download broadcast ephemeris from CDDIS FTP"""
          ftp = ftplib.FTP("cddis.gsfc.nasa.gov") 
          ftp.login('', '') 

          saveDir = os.path.join( workingDir,self.subdir)
          if not os.path.exists(saveDir):
              os.makedirs(saveDir)
          t=t1
          while t<t2:
            doy = t.timetuple().tm_yday
            y = t.year   
            y2 = '{:02}'.format(y%100)

            ftpdir = '/pub/gps/data/daily/{}/{:03}/{}{}'.format(t.year,doy,y2,self.SsLitera)
            t = t + dt.timedelta(days=1)
            if ftpdir!= ftp.pwd():
               print( ftp.cwd(ftpdir))
            #cod"{w}{d}".eph.Z
            #cod19633.eph.Z

            curfile = 'brdc{:03}0.{}{}.Z'.format(doy, y2, self.SsLitera)
           
            savepath  = os.path.join(saveDir, curfile)
            if os.path.exists(os.path.splitext(savepath)[0]):
               continue

            print( savepath)
            try:
                ftp.retrbinary("RETR " + curfile, open(savepath, 'wb').write)
                resfile  = dld.unzip(saveDir,curfile)
                self._toRemove.append(resfile)
            except BaseException as e:
                print( 'An exception has occured:'+  str(e))

class DownloadBceGLONASS(DownloadBCE):
     """download GPS broadcast ephemeris from CDDIS FTP"""
     def __init__(self):
        """Constructor"""
        DownloadBCE.__init__(self, 'g')

class DownloadBceGPS(DownloadBCE):
     """download GLONASS broadcast ephemeris from CDDIS FTP"""
     def __init__(self):
        """Constructor"""
        DownloadBCE.__init__(self, 'n')
