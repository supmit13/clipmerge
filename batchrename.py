import os, sys, re, time
import glob



if __name__ == "__main__":
    if sys.argv.__len__() < 3:
        print("Error - Insufficient parameters: python %s <directory_path> <int_num>"%sys.argv[0])
        sys.exit()
    dirpath = sys.argv[1]
    intnum = sys.argv[2]
    extension = "*"
    if sys.argv.__len__() > 3:
        extension = sys.argv[3]
    endslashpattern = re.compile("\/$")
    dirpath = endslashpattern.sub("", dirpath)
    if not os.path.isdir(dirpath):
        print("Error - Given directory path '%s' does not exist"%dirpath)
        sys.exit()
    try:
        intnum = int(intnum) # Convert number to int if user provides a floating point number
    except:
        print("Error: %s"%sys.exc_info()[1].__str__())
        sys.exit() # In case of any error (like a non-numeric string has been entered), break out.
    # Read contents of given dirpath
    allentries = glob.glob(dirpath+os.path.sep+"*.%s"%extension)
    numctr = intnum
    fcount = 0
    for ent in allentries:
        if os.path.exists(ent) and not os.path.isdir(ent): # We will rename files and softlinks only, not directories
            fnameext = os.path.basename(ent)
            fparts = fnameext.split(".")
            fname = fparts[0]
            fext = ""
            if fparts.__len__() > 1:
                fext = fparts[1]
            fdir = os.path.dirname(ent)
            targetname = str(numctr) + "." + fext
            targetpath = fdir + os.path.sep + targetname
            try:
                os.rename(ent, targetpath)
            except:
                print("Could not rename file '%s': %s"%(ent, sys.exc_info()[1].__str__()))
            numctr += 1
            fcount += 1
    print("Done! %s files renamed\n"%fcount)

"""
How to run: python batchrename.py /home/supmit/work/clipmerger/test/batchtest 60 "wav"
If you do not provide the last parameter, it will rename all files with all extensions.

"""

