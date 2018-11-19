import datetime as dt
import argparse
import configparser
import os
import ftplib
import subprocess
import GeoNetwork

import auxiliary as aux
import FtpDownload as dldBase
import FtpDownloadSp3 as dldSp3
import FtpDownloadBce as dldBce

tstart = dt.datetime.now()
agrParser = argparse.ArgumentParser()
agrParser.add_argument('--file', help='path to file with processing configuration', required=True)
agrParser.add_argument('--rd', help='(remove data) remove all downloaded data after processing finish ', required=False)
args = agrParser.parse_args()

rd = False
try:
    rd = aux.str2bool(args.rd)
except: 
    rd = False

cgfPath = args.file
workingDir = os.path.dirname(cgfPath)
sites = []
t_start = dt.datetime.now()
t_end = dt.datetime.now()
dt_ = 1

with open(cgfPath) as fp:
    cfgParser = configparser.ConfigParser()
    cfgParser.read_file(fp)
    appFile =  cfgParser['DEFAULT']['AppPath']
    sites = cfgParser['DEFAULT']['Sites'].split('#')[0].split(' ')
    t_start =  dt.datetime.strptime( cfgParser['DEFAULT']['t1'],'%Y-%m-%d')
    t_end =  dt.datetime.strptime( cfgParser['DEFAULT']['t2'],'%Y-%m-%d')
    dt_ = dt.timedelta(days= int(cfgParser['DEFAULT']['dt']))
    strNet = cfgParser['DEFAULT']['Network']
    geoNet = GeoNetwork.GeoNetwork[strNet]

#dld.DownloadCodeClk(),dld.DownloadGfzClk()
dlds = []
if(geoNet==GeoNetwork.GeoNetwork.TPS):
    for it in sites:
        dlds.append(dldBase.DownloadTps(it))
elif(geoNet==GeoNetwork.GeoNetwork.IGS):
    dlds.append(dldSp3.DownloadGfzEph(daysgap=0))
    for it in sites:
        dlds.append(dldBase.DownloadRnx30sCddis(it))


#clear observation direcory
dldBase.clear_directory(os.path.join( workingDir,"OBS"))

t1=t_start
while t1<t_end:
    t2 = t1+dt_
    try:
        print(t1)
        any(obj.removeData() for obj in dlds)
        any(obj.download(t1, t2, workingDir) for obj in dlds )
        print('---\nreal precessing part started...')
        #subprocess.check_call(appFile+' '+cgfPath)
        print('real precessing part finished\n---')

    except ftplib.all_errors as e:
       print (e)
       print ('processing skipped for batch from {} to {}'.format(t1,t2))
       any(obj.clearWorkingDir(workingDir) for obj in dlds)

    t1 += dt_
if(rd):
    any(obj.removeData() for obj in dlds)
    any(obj.clearWorkingDir(workingDir) for obj in dlds)
tfinish = dt.datetime.now()
print('Elapsed time: ' +str(tfinish-tstart))