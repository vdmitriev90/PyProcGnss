import datetime as dt
import ftplib 
import os, sys, os.path

import re
import shutil

import FtpDownload as dld

class DownloadOrbits(dld.DownloadBase):
     """download CODE  products from CDDIS FTP"""
     
     def __init__(self, subdir,agency, ext, daysgap):
        """Constructor"""
        dld.DownloadBase.__init__(self, subdir)
        self.agency = agency
        self.ext = ext
        self.gap = dt.timedelta(daysgap)

     def changeTimeLimits(self, t1, t2):
        """Change time limits. Do nothing by default"""
        _t1 = t1 - self.gap
        _t2 = t2 + self.gap
        return _t1, _t2     

     def _download(self, t1, t2, workingDir):
        """download CODE products from CDDIS FTP"""

        ftp = ftplib.FTP("cddis.gsfc.nasa.gov") 
        ftp.login('', '')

        saveDir = os.path.join( workingDir,self.subdir)
        if not os.path.exists(saveDir):
            os.makedirs(saveDir)
        l = t2-t1-self.gap*2
        t=t1
        while t<t2:

            week =  dld.utcToGPSWeek(t)
            t += dt.timedelta(days=1)
            ftpdir = '/pub/gps/products/{:04}'.format(week[0])
            if ftpdir!= ftp.pwd():
                print( ftp.cwd(ftpdir))

            curfile = '{}{:04}{}.{}.Z'.format(self.agency, week[0], week[1], self.ext)
           
            savepath  = os.path.join(saveDir, curfile)
            resFile = os.path.splitext(savepath)[0]
            if os.path.exists(resFile):
               if t- t1 <=l: 
                  self._toRemove.append(resFile)
               continue

            print( savepath)
            try:
                ftp.retrbinary("RETR " + curfile, open(savepath, 'wb').write)
                resFile = dld.unzip(saveDir,curfile)
                if t- t1 <=l: 
                    self._toRemove.append(resFile)
            except BaseException as e:
                print( 'An exception has occured:'+  str(e))

class DownloadCodeEph(DownloadOrbits):
     """download CODE SP3 products from CDDIS FTP"""
     def __init__(self, daysgap=1):
        """Constructor"""
        DownloadOrbits.__init__(self, 'EPH', 'cod', 'eph', daysgap)

class DownloadCodeClk(DownloadOrbits):
     """download CODE 30 sec. clock products from CDDIS FTP"""
     def __init__(self, daysgap=1):
        """Constructor"""
        DownloadOrbits.__init__(self, 'CLK_30S','cod', 'clk', daysgap)

class DownloadGfzEph(DownloadOrbits):
     """download GFZ SP3 products from CDDIS FTP"""
     def __init__(self, daysgap=1):
        """Constructor"""
        DownloadOrbits.__init__(self, 'EPH','gfz', 'sp3', daysgap)

class DownloadGfzClk(DownloadOrbits):
     """download GFZ SP3 products from CDDIS FTP"""
     def __init__(self, daysgap=1):
        """Constructor"""
        DownloadOrbits.__init__(self, 'CLK_30S','gfz', 'clk', daysgap)
