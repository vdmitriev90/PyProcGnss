import datetime as dt
import argparse
import configparser
import os
import ftplib
import subprocess

import auxiliary as aux
import FtpDownload as dld

# example of command line argumants 
# --file D:\_temp\pProc\ppScript.ini --rd 1
agrParser = argparse.ArgumentParser()
agrParser.add_argument('--file', help='path to file with processing configuration', required=True)
agrParser.add_argument('--rd', help='(remove data) remove all downloaded data after processing finish ', required=False)
args = agrParser.parse_args()

cgfPath = args.file
rd = False
try:
    rd = aux.str2bool(args.rd)
except: 
    rd = False

cfgParser = configparser.ConfigParser()
cfgParser.read(cgfPath)

appFile =  cfgParser['DEFAULT']['AppPath']
cfgFile = cfgParser['DEFAULT']['ConfigPath']
workingDir = os.path.dirname(cfgFile)

sites = cfgParser['DEFAULT']['Sites'].split('#')[0].split(' ')
sites = list(filter(lambda x: len(x)==4,sites))

t_start =  dt.datetime.strptime( cfgParser['DEFAULT']['t1'],'%Y-%m-%d')
t_end =  dt.datetime.strptime( cfgParser['DEFAULT']['t2'],'%Y-%m-%d')
dt_ = dt.timedelta(days= int(cfgParser['DEFAULT']['dt']))

#dld.DownloadCodeClk(),dld.DownloadGfzClk()
dlds = [dld.DownloadGfzEph(),dld.DownloadBceGLONASS(),dld.DownloadBceGPS(),dld.DownloadRnx15sTps(sites[0])]

if len(sites) >1:
    dlds.append(dld.DownloadRnx15sTps(sites[1]))
#else:
 #   dlds.append()

t1=t_start

#clear observation direcory
dld.clear_directory(os.path.join( workingDir,"OBS"))

while t1<t_end:
    t2 = t1+dt_
    try:
        print(t1)
        any(obj.removeData() for obj in dlds)
        any(obj.download(t1, t2, workingDir) for obj in dlds )
        print('---\nreal precessing part started...')
        subprocess.check_call(appFile+' '+cfgFile)
        print('real precessing part finished\n---')

    except ftplib.all_errors as e:
       print (e)
       print ('processing skipped for batch from {} to {}'.format(t1,t2))
       any(obj.clearWorkingDir(workingDir) for obj in dlds)

    t1 += dt_
if(rd):
    any(obj.removeData() for obj in dlds)
    any(obj.clearWorkingDir(workingDir) for obj in dlds)