import abc
import datetime as dt
import ftplib 
import os, sys, os.path
import subprocess
import re
import shutil

recrx = re.compile(r'(\.[\d]{2})d')

def clear_directory(folder):
    """remove all files and subdirectories in given catalog"""
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
           if os.path.isfile(file_path): os.unlink(file_path)
           elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)

def padd(source, padding):
    return padding+source+padding

def utcToGPSWeek(gpst_calendar):
    """ Returns the GPS week, the GPS day, and the seconds 
        and microseconds since the beginning of the GPS week """
    
    epoch = dt.datetime(1980,1,6)
    tdiff = gpst_calendar - epoch
    gpsweek = tdiff.days // 7 
    gpsdays = tdiff.days - 7*gpsweek         
    gpsseconds = tdiff.seconds + 86400* (tdiff.days -7*gpsweek)
    return gpsweek, gpsdays, gpsseconds, tdiff.microseconds


def unzip(dir,file):
    fullPath  = os.path.join( dir, file)
    command = '"7z.exe" e -aoa -bso0 -bsp0 ' + padd(fullPath,'\"') + ' -o' + padd(dir,'\"')
          
          #os.system(command)
    subprocess.check_call(command)
          
          #remove source archive 
    os.remove(fullPath)
    #return new filename
    return os.path.splitext(fullPath)[0]

class DownloadBase(object):
    """download data from FTP"""
    _toRemove = list()
         
    def __init__(self, subdir=None):
        """Constructor"""
        self.subdir = subdir

    @abc.abstractmethod
    def _download(self, t1, t2, workingDir):
        """download data from FTP"""
    
    def changeTimeLimits(self, t1, t2):
        """Change time limits. Do nothing by default"""
        return t1, t2

    def download(self, t1, t2, workingDir):
        """download data from FTP"""
        self._toRemove = []
        newLims = self.changeTimeLimits( t1, t2)
        self._download(newLims[0],newLims[1], workingDir)

    def removeData(self):
        """remove unused data """
        for f in self._toRemove:
            os.remove(f)

    def clearWorkingDir(self, workingDir):
        """remove unused data """
        clear_directory(os.path.join(workingDir,self.subdir))
        self._toRemove.clear()

class DownloadObs(DownloadBase):

    def clearWorkingDir(self, workingDir):
        """remove all changes """
        clear_directory(os.path.join(workingDir,'OBS'))
        self._toRemove.clear()

class DownloadTps(DownloadObs):
    """download Tps"""

    def _download(self, t1, t2, workingDir):
        """download TPS Obs from FTP"""

        ftp = ftplib.FTP("mos-nets") 
        ftp.login("data", "ftpdata")      
        saveDir = os.path.join( workingDir,"OBS",self.subdir)

        if not os.path.exists(saveDir):
           os.makedirs(saveDir)   

        t=t1
        while t<t2:
            
            directory = '/tps/{}/{:02}/{}-{:02}-{:02}/{}/'.format(t.year,t.month,str(t.year)[2:],t.month,t.day,self.subdir)
         
            try:
                print( ftp.cwd(directory))
            except ftplib.all_errors as e:
                print( str(e))
                raise
            files = ftp.nlst()

            for f in files: 
                savepath  = os.path.join( saveDir, f)
                print( savepath)
                
                ftp.retrbinary("RETR " + f ,open(savepath, 'wb').write)
                if os.path.splitext()[1] != '.tps':
                    self._toRemove.append( unzip( saveDir, f))
            t += dt.timedelta(days=1)

        ftp.quit()

class DownloadRinex15Sec(DownloadObs):


    @staticmethod
    def unzip_uncrx(dir,file):
          unZippedPath = unzip(dir,file)
          command = 'crx2rnx.exe' + ' -f ' + padd(unZippedPath,'\"')
          subprocess.check_call(command)

          #remove crx file
          os.remove(unZippedPath)
          return re.sub(recrx,r'\1o', unZippedPath)

    def _download(self, t1, t2, workingDir):
        """download Rinex Obs from FTP"""

        ftp = ftplib.FTP("mos-nets") 
        ftp.login("data", "ftpdata") 

        saveDir = os.path.join( workingDir,"OBS",self.subdir)
        if not os.path.exists(saveDir):
            os.makedirs(saveDir)

        t=t1
        while t<t2:
             # string path = string.Format("ftp://{0}RINEX/{1}/{2}/{3}/{4}/", Host, dti.Year, m2, date, Site.ID);
            directory = '/RINEX/{}/{:02}/{}-{:02}-{:02}/{}/'.format(t.year,t.month,str(t.year)[2:],t.month,t.day, self.subdir)
            print( directory)

            try:
                ftp.cwd(directory)
            except ftplib.all_errors as e:
                print( str(e))
                raise
            files = ftp.nlst()

            for f in files: 
                if f[-4:]=='d.gz':
                    savepath  = os.path.join( saveDir, f)
                    print( savepath)
                    ftp.retrbinary("RETR " + f ,open(savepath, 'wb').write)
                    self._toRemove.append(DownloadRinex15Sec.unzip_uncrx(saveDir,f))

            t += dt.timedelta(days=1)

        ftp.quit()


class DownloadOrbits(DownloadBase):
     """download CODE  products from CDDIS FTP"""
     
     
     def __init__(self, subdir,agency, ext):
        """Constructor"""
        DownloadBase.__init__(self, subdir)
        self.agency = agency
        self.ext = ext
        self.gap = dt.timedelta(days=1)


     def changeTimeLimits(self, t1, t2):
        """Change time limits. Do nothing by default"""
        _t1 = t1- self.gap
        _t2 = t2+ self.gap
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

            week =  utcToGPSWeek(t)
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
                resFile = unzip(saveDir,curfile)
                if t- t1 <=l: 
                    self._toRemove.append(resFile)
            except BaseException as e:
                print( 'An exception has occured:'+  str(e))

class DownloadCodeEph(DownloadOrbits):
     """download CODE SP3 products from CDDIS FTP"""
     def __init__(self):
        """Constructor"""
        DownloadOrbits.__init__(self, 'EPH', 'cod', 'eph')
class DownloadCodeClk(DownloadOrbits):
     """download CODE 30 sec. clock products from CDDIS FTP"""
     def __init__(self):
        """Constructor"""
        DownloadOrbits.__init__(self, 'CLK_30S','cod', 'clk')

class DownloadGfzEph(DownloadOrbits):
     """download GFZ SP3 products from CDDIS FTP"""
     def __init__(self):
        """Constructor"""
        DownloadOrbits.__init__(self, 'EPH','gfz', 'sp3')

class DownloadGfzClk(DownloadOrbits):
     """download GFZ SP3 products from CDDIS FTP"""
     def __init__(self):
        """Constructor"""
        DownloadOrbits.__init__(self, 'CLK_30S','gfz', 'clk')

class DownloadBCE(DownloadBase):
      """download broadcast ephemeris from CDDIS FTP"""          
      def __init__(self,SsLitera):
          """Constructor"""
          DownloadBase.__init__(self, 'NAV')
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
                resfile  = unzip(saveDir,curfile)
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

if __name__ == "__main__":
   #d =  DownloaderRinex15Sec("DRBN")
   d =  DownloadBceGPS()
   iday = 200
   t2 = dt.datetime.now() - dt.timedelta(days=iday)
   print( t2)
   t1 = t2 - dt.timedelta(days=10)
   print( t1)
   d.download(t1,t2,"D:\_temp\python")
