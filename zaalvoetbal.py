#!/usr/bin/env python3

from __future__ import print_function
from subprocess import call, check_output
from datetime import datetime
import sys
import tempfile
import argparse
import os
import re
import urllib.request

if sys.version_info[0] < 3:
    sys.stderr.write(r'Please use Python 3\n')
    sys.exit(1)

p = argparse.ArgumentParser()
p.add_argument('-team', type=str, default='Seedorf',
               help='Team name')
p.add_argument('-update', action='store_true', help='Download new pdf file')
p.add_argument('-url', type=str,
               default=r'https://usc.uva.nl/sport/zaalvoetbalcompetitie/',
               help='URL of USC futsal page')
p.add_argument('-db', type=str, default='zaalvoetbal.db',
               help='File name of database')

args = p.parse_args()

if args.update:
    page = urllib.request.urlopen(args.url).read().decode('utf-8')
    pdf_pat = [re.compile(r'http.*speelschema.*\.pdf', re.I),
               re.compile(r'http.*bekerschema.*\.pdf', re.I)]
    pdf_files = []
    for p in pdf_pat:
        pdf_files += p.findall(page)

    output = ""
    for pdf in pdf_files:
        with tempfile.NamedTemporaryFile(suffix='.pdf') as fp:
            call(['wget', '--quiet', pdf, '-O', fp.name])
            tmp = check_output(['pdftotext', '-layout', fp.name, '-'])
            # Decode byte string
            output += tmp.decode(r'utf-8')
    with open(args.db, 'w') as db:
        db.write(output)
else:
    with open(args.db, 'r') as db:
        output = db.read()

lines = output.splitlines()

# To match the team name
team_pat = re.compile(args.team, re.I)

# To match a date
date_pat = re.compile(r'(\d\d/\d\d)')

# To match a time
time_pat = re.compile(r'(\d\d:\d\d)')

# To match the team names in a line
teams_pat = re.compile(r'[0-9A-Z]{5}\s*'   # e.g. 02B29
                       r'([^-]+)'          # first team
                       r'-\s*'             # separator
                       r'(.*)\d\d:\d\d')   # second team followed by time

now = datetime.now()
year = str(now.year)

match_lines = []
play_dates = []
ref_dates = []
home_teams = []
away_teams = []

# Search for lines matching the team pattern
for i in range(len(lines)):
    if team_pat.search(lines[i]):
        match_lines.append(i)

for ix in match_lines:
    # Find date pattern by searching backwards through the lines
    for i in range(ix, -1, -1):
        m = date_pat.search(lines[i])
        if m: break
    date = m.group(1)

    # Find play/referee times
    times = time_pat.findall(lines[ix])

    play_date = datetime.strptime(' '.join(
        [year, date, times[0]]), '%Y %d/%m %H:%M')
    if play_date > now and (play_date - now).days < 180:
        if len(times) > 1:
            ref_date = datetime.strptime(' '.join(
                [year, date, times[1]]), '%Y %d/%m %H:%M')
        else:
            ref_date = play_date
        play_dates.append(play_date)
        ref_dates.append(ref_date)
        m = teams_pat.search(lines[ix])
        home_teams.append(m.group(1).strip())
        away_teams.append(m.group(2).strip())

print(r'''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>USC zaalvoetbal schema</title>

    <link rel="stylesheet" type="text/css" href="style.css">
  </head>
  <body>

    <div class="header">
      <div class="image">
        <img src="images/logo-usc.png" alt="USC logo" height="60" width="42">
      </div>
      <div class="title">
        <h1>USC zaalvoetbal schema</h1>
      </div>
    </div>
''')

prev_month = -1
for i in range(len(play_dates)):
    month = play_dates[i].month

    if month != prev_month:
        if prev_month != -1:
            print(r'</div>')
        print(r'<div class="grid-container">')
        print(r'  <div class="month">')
        print(r'    <h2 align="center">{}</h2>'.format(
            play_dates[i].strftime(r'%B')))
        print(r'  </div>')
        prev_month = month

    print(r'')
    print(r'<div class="grid-item">')
    print(r'  <div class="time">')
    print(r'    <h3>{}</h3>'.format(
        play_dates[i].strftime(r'%d %B - %H:%M')))
    if team_pat.search(home_teams[i]):
        print(r'    <h5>&nbsp + fluiten {}</h5>'.format(
            ref_dates[i].strftime(r'%H:%M')))
    print(r'  </div>')
    print(r'  <div class="match">')
    print(r'    <div id="left">')
    print(r'      <h2 align="right">{}</h2>'.format(home_teams[i].strip()))
    print(r'    </div>')
    print(r'    <div id="center">')
    print(r'      <img src="images/versus.png" class="versus" align="center" alt="USC logo" height="32" width="32">')
    print(r'    </div>')
    print(r'    <div id="right">')
    print(r'      <h2 align="left">{}</h2>'.format(away_teams[i].strip()))
    print(r'    </div>')
    print(r'  </div>')
    print(r'</div>')
    print(r'')

print(r'''</div>
  </body>
</html>
''')
