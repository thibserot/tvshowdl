#!/usr/bin/python
# -*- coding: utf-8 -*-

import re,sys,os, difflib, urllib2
from feedparser import parse
from urllib import urlretrieve

OUTPUT_DIR = "./"
TVSHOW_FILE = OUTPUT_DIR + "tvshows.txt"
TORRENT_FOLDER = OUTPUT_DIR + "torrent/"
WANT_HD = False

def isHD(quality):
    if not quality:
        return False
    else:
        for q in quality:
            if q in set(["720P","1080P"]):
                return True
        return False

def checkURL(url):
    try:
        f = urllib2.urlopen(urllib2.Request(url))
        deadLinkFound = True
    except (ValueError,urllib2.HTTPError):
        print sys.exc_info()
        deadLinkFound = False
    return deadLinkFound



def downloadTorrent(url):
    if not checkURL(url):
        print "Invalid url",url
        return -1

    output = url.split("/")[-1]
    try:
        urlretrieve(url,TORRENT_FOLDER + output)
    except IOError, e:
        print "IOError"
        return -1
    return 0


if len(sys.argv) == 2:
    hd = sys.argv[1]
    if hd.upper() == "HD":
        WANT_HD = True
    elif hd.upper() == "NO_HD":
        WANT_HD = False
    else:
        print "Unknown parameter",hd
        sys.exit()

if not os.path.exists(TVSHOW_FILE):
    print "No tvshow file, aborting"
    sys.exit()

if not os.path.exists(TORRENT_FOLDER):
    os.makedirs(TORRENT_FOLDER)



# Read the tvshow file
f = open(TVSHOW_FILE,"r")
tvshows = {}
for line in f:
    show = line.strip().split(u"\t")
    if len(show) == 1:
        tvshows[show[0]] = [ 0, 0]
    else:
        tvshows[show[0]] = [int(show[1]), int(show[2])]
f.close()

print "tvshow to monitore :",tvshows
print "looking for HD :",WANT_HD
# Read the RSS feed
myfeed = parse("http://www.ezrss.it/feed")

matches = {}

for item in myfeed['entries']:
    #for k,v in item.items():
    #    print k,"=>",v
    #print item["title"],item["link"]
    summary = item["summary"]
    summary = summary.strip().split(";")
    summary = [[j.strip() for j in i.split(":")] for i in summary]
    infos = {}
    for s in summary:
        infos[s[0]] = s[1]
    infos["link"] = item["link"]
    if len(infos["link"]) < 10:
        continue
    quality = re.search("\[([^\]]*)\]",item["title"])
    if quality:
        quality = set(quality.group(1).upper().split(" - "))
    infos["quality"] = quality
    infos["HD"] = isHD(infos["quality"])
    # Now we have in infos : show name, episode, season, url, quality
    if not infos.has_key(u"Show Name") or not infos.has_key(u"Episode") or not infos.has_key(u"Season"):
        continue
    else:
        infos["Episode"] = int(infos["Episode"])
        infos["Season"] = int(infos["Season"])
        res = difflib.get_close_matches(infos[u"Show Name"],tvshows.keys(),1)
        if len(res) == 1:
            #print "We found a match"
            infos["Show"] = res[0]
            if not matches.has_key(res[0]):
                matches[res[0]] = []
            matches[res[0]] += [infos,]

# Analyse of every match we found to download only accurates ones
final = []
for show,result in matches.items():
    if len(result) == 0:
        pass
    elif len(result) == 1:
        # We got only one result, let's download it
        if WANT_HD or not result[0]["HD"]:
            season = result[0]["Season"]
            epsode = result[0]["Episode"]
            if season < tvshows[show][0]:
                 continue
            elif season == tvshows[show][0] and episode <= tvshows[show][1]:
                continue
            else:
                final += [result,]
    else:
        # Check if we got several episodes and just keep one of each
        #ep = result[0]["Episode"]
        #season = result[0]["Season"]
        version = {}
        #if not version.has_key(season):
        #    version[season] = {}
        #version[season][ep] = result[0]
        for r in result:
            ep     = r["Episode"]
            season = r["Season"]
            if WANT_HD or not r["HD"]:
                if version.has_key(season) and version[season].has_key(ep):
                    pass
                else:
                    if not version.has_key(season):
                        version[season] = {}
                    version[season][ep] = r
        for season in version:
            for episode in version[season]:
                if season < tvshows[show][0]:
                    continue
                elif season == tvshows[show][0] and episode <= tvshows[show][1]:
                    continue
                else:
                    final += [version[season][episode],]


for f in final:
    print "Downloading",f["Show"],"%02dx%02d" % (f["Season"], f["Episode"]),
    if f["HD"]:
        print "in HD"
    else:
        print "not in HD"

    res = downloadTorrent(f["link"])
    if res == 0:
        # Update the list of shows
        if f["Season"] > tvshows[f["Show"]][0] or (f["Season"] == tvshows[f["Show"]][0] and f["Episode"] > tvshows[f["Show"]][1]):
            tvshows[f["Show"]] = [f["Season"],f["Episode"]]




s_keys = sorted(tvshows.keys())
f = open(TVSHOW_FILE,"w")
for s in s_keys:
    if tvshows[s][0] == 0 and tvshows[s][1] == 0:
        f.write(s + u"\n")
    else:
        f.write(s + u"\t" + str(tvshows[s][0]) + u"\t" + str(tvshows[s][1]) + u"\n")
f.close()

