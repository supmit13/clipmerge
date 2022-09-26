import os, sys, re, time
from datetime import datetime
import ffmpeg
import requests
import urllib
from urllib.parse import urlencode
import random
import subprocess
import glob

UNIQUE_FILES = {}

def generaterandomnumber(maxnum, minnum=0):
    return random.randint(minnum, maxnum)


def getvideoduration(vidfile):
    cmd = "ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 %s"%vidfile
    try:
        outstr = subprocess.check_output(cmd, shell=True)
    except:
        print("Could not find the duration of '%s' - Error: %s"%(vidfile, sys.exc_info()[1].__str__()))
        return -1
    outstr = outstr.decode('utf-8')
    outstr = outstr.replace("\n", "").replace("\r", "")
    wspattern = re.compile("\s*", re.DOTALL)
    outstr = wspattern.sub("", outstr)
    durationinseconds = float(outstr)
    return durationinseconds


def getaudioduration(audfile="test/audiofiles/mixkit-stadium-crowd-light-applause-362.wav"):
    cmd = "ffprobe -v error -select_streams a:0 -show_entries stream=duration -of default=noprint_wrappers=1:nokey=1 %s"%audfile
    try:
        outstr = subprocess.check_output(cmd, shell=True)
    except:
        print("Could not find the duration of '%s' - Error: %s"%(vidfile, sys.exc_info()[1].__str__()))
        return -1
    outstr = outstr.decode('utf-8')
    outstr = outstr.replace("\n", "").replace("\r", "")
    wspattern = re.compile("\s*", re.DOTALL)
    outstr = wspattern.sub("", outstr)
    durationinseconds = float(outstr)
    return durationinseconds




if __name__ == "__main__":
    if sys.argv.__len__() < 3:
        print("Insufficient parameters: python %s 'video_file_path' 'audio_dir_path' 'audio_ext'"%sys.argv[0])
        sys.exit()
    videofile = sys.argv[1]
    audiodirpath = sys.argv[2]
    audio_ext = "wav"
    if sys.argv.__len__() > 3:
        audio_ext = sys.argv[3]
    endslashpattern = re.compile("\/$")
    audiodirpath = endslashpattern.sub("", audiodirpath)
    vdur = getvideoduration(videofile)
    print(vdur)
    allaudiofiles = glob.glob(audiodirpath + os.path.sep + "*.%s"%audio_ext) # Assuming we will get audio as wav files
    audiocount = allaudiofiles.__len__()
    #print("\n".join(allaudiofiles))
    adur = 0
    audiolist = []
    delta, deltafile = 0, None
    while vdur - adur > 0:
        r = generaterandomnumber(audiocount-1)
        selectedaudiofile = allaudiofiles[r]
        if selectedaudiofile in UNIQUE_FILES.keys():
            continue
        #print(selectedaudiofile)
        UNIQUE_FILES[selectedaudiofile] = 1
        # Get duration of selected audio file
        audioduration = getaudioduration(selectedaudiofile)
        adur += audioduration
        #print(adur)
        if adur > vdur: # Check how much longer audio file is
            delta = audioduration - (adur - vdur)
            deltafile = selectedaudiofile
            break
        else:
            audiolist.append(selectedaudiofile)
        unique_files = UNIQUE_FILES.keys()
        if unique_files.__len__() == allaudiofiles.__len__(): # We possibly have a situation where we have used up all audio files and yet we haven't got enough time with all those audio files.
            print("Possible infinite loop condition. Breaking out.")
            break
    # if we have a deltafile, clip it at delta seconds from start
    if deltafile is not None:
        tmin = '00'
        tsec = str(int(delta))
        if delta > 60:
            tmin = int(int(delta)/60)
            tsec = int(delta - tmin * 60)
        if str(tmin).__len__() < 2:
            tmin = '0' + str(tmin)
        if str(tsec).__len__() < 2:
            tsec = '0' + str(tsec)
        tmin = str(tmin)
        tsec = str(tsec)
        clippedaudiofilename = os.path.basename(deltafile).split(".")[0] + "_clipped." + os.path.basename(deltafile).split(".")[1]
        clippedaudiofile = audiodirpath + os.path.sep + clippedaudiofilename
        audclipcmd = "ffmpeg -ss 00:00:00 -i %s -c:a copy -to 00:%s:%s %s"%(deltafile, tmin, tsec, clippedaudiofile)
        print(audclipcmd)
        subprocess.call(audclipcmd, shell=True)
        if os.path.exists(clippedaudiofile):
            audiolist.append(clippedaudiofile)
        else:
            audiolist.append(deltafile)
    # Concatenate all audio files in audiolist to form a single audio track
    minusistr, n, filterstr = "", 0, ""
    for afile in audiolist:
        minusistr += "-i %s "%afile
        n += 1
        filterstr = filterstr + "[%s:0]"%(n-1)
    aconcatcmd = "ffmpeg -y %s -filter_complex '%sconcat=n=%s:v=0:a=1[out]' -map '[out]' concataudio.wav"%(minusistr, filterstr, n)
    print(aconcatcmd)
    subprocess.call(aconcatcmd, shell=True)
    outvideo = "finalvideo.mp4"
    if os.path.exists("concataudio.wav"): # Concatenation was successful, so do the overlay of the video with this audio file
        overlaycmd = "ffmpeg -y -i %s -i concataudio.wav -map 0 -map 1 -c copy %s"%(videofile, outvideo)
        #overlaycmd = "ffmpeg -y -i %s -i concataudio.wav -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 %s"%(videofile, outvideo)
        subprocess.call(overlaycmd, shell=True)
    if os.path.exists(outvideo):
        print("Process completed successfully")
    else:
        print("Process failed")
    print("Done!")


"""
How to run:
python clipmerge.py video_file_path audio_dir_path

References: 
https://superuser.com/questions/650291/how-to-get-video-duration-in-seconds
https://superuser.com/questions/587511/concatenate-multiple-wav-files-using-single-command-without-extra-file
"""


