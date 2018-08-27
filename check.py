import FtpDownload
import datetime as dt
import sqlite3
import matplotlib.pyplot as plt
import argparse

def check():
    parser = argparse.ArgumentParser()
    parser.add_argument('--site', help='site to be processed', required=True)
    #parser.add_argument("-v",'--vvv', help='test argument', required=True)
    args = parser.parse_args()
    site = args.site
    
    print (site)
    conn = sqlite3.connect("MOS-NETS-Stat.db") 
    cursor = conn.cursor()
    #stmt = "SELECT DISTINCT SITE FROM DATA;"
    stmt = "SELECT TIME, size FROM DATA WHERE SITE = '{0}' ORDER BY Time;".format(site)
    cursor.execute(stmt)
    print (cursor) 
    #for res in cursor.fetchall():
    res =  cursor.fetchall()
    #for it in res: print (it)

    times = list(map( lambda x: dt.datetime.strptime(x[0],'%Y-%m-%d %H:%M:%S'), res))
    t0 =times[0]
    te = times[-1]
    args = list()
    values = list()
    while t0<te:
        args.append(t0)
        if t0 in times:
            values.append(1)
        else:
            values.append(0)
        t0 +=dt.timedelta(hours=1)

    plt.plot(args,values,'ro')
    plt.show()
    conn.close()

if __name__ == "__main__":
    check()
