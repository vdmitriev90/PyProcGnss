import ftplib
import datetime
import sqlite3
import re


def download():
    """download TPS Obs from FTP"""

    hours = "abcdefghijklmnopqrstuvwx"
    lit2hour = {a: hours.index(a) for a in hours }

    conn = sqlite3.connect("MOS-NETS-Stat.db") 
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS `DATA`  ( `TIME` TEXT, `SITE` TEXT, `size` INTEGER );""")
    conn.commit()

    ftp = ftplib.FTP("mos-nets") 
    ftp.login("data", "ftpdata")    
    ftp.cwd('tps')
    years =  ftp.nlst()
    for y in years:
       yi = int(y)
       print (yi)
       ftp.cwd(y)  
       month =  ftp.nlst()
       for m in month:
          ftp.cwd(m)
          mi = int(m)
          days =  ftp.nlst()
          for d in days:
             print (d)
             try:
               di = int(d[6:])
             except BaseException as e:
               print( str(e))
               continue
             ftp.cwd(d)
             sites =  ftp.nlst()
             for s in sites:
                ftp.cwd(s)
                files =  ftp.nlst()
                for f in files:
                   pattern= r'([\d]{4})([\w])(.tps)'
                   res = re.search(pattern,f)
                   if res!=None and len(res.regs)==4:
                      lit = res.group(2)
                      if lit not in lit2hour:
                        continue
                      hour = lit2hour[lit]
                      size = ftp.size(f)
                      cursor.execute("""INSERT INTO DATA VALUES (?, ?, ?); """,(str(datetime.datetime(yi,mi,di,hour)),s,str(size)))
                ftp.cwd("../")
             ftp.cwd("../")
          ftp.cwd("../")
       conn.commit()
       ftp.cwd("../")
      
    conn.close()

if __name__ == "__main__":
    download()
