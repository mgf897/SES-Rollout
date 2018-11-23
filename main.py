
"""
SES Rollout
"""

__author__ = "mgf897, ssfivy"
__version__ = "0.1.0"
__license__ = "CC SA"

import argparse
import subprocess
import sys
import os
import sys
import time
import glob
import serial.tools.list_ports
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup

if sys.platform.startswith('win32'):
    import win32com.client

trainingURL = "https://trainbeacon.ses.nsw.gov.au"
trainingURL_login = "https://identitytrain.ses.nsw.gov.au/core/login"

liveURL = "" # TODO: Fill this infromation
liveURL_login = "" # TODO: Fill this information

initial_wait = 10
jobs_recent_enough = 30
jobs_refresh_delay = 10

# version number check: Require 3.6
if sys.version_info < (3, 6) :
    raise NotImplementedError('This script requires Python version 3.6 or later')

def list_ports():
    ports = serial.tools.list_ports.comports()
	
    print("Available comm ports")
    for port, desc, hwid in sorted(ports):
        print(f"{port}: {desc} [{hwid}]") 

    return(ports)
    
def sayText(sentence):
    if sys.platform.startswith('linux'):
        # Festival tts engine is written partly with Scheme so its syntax is a bit exotic
        cmd = ['festival', '-b', '(voice_cmu_us_slt_arctic_hts)',  f'(SayText "{sentence}")']
        subprocess.run(cmd)
    elif sys.platform.startswith('win32'):
        # Completely untested, might neex extra dependencies. Please update READMe when you got this working.
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Speak(sentence)


def announceJob(job):
    print(job)
    # Generate sentence to speak
    words = []
    words.append('There is an incident requiring ')
    words.append(job['priority'])
    words.append(' response! ')

    words.append(' It is a ')
    words.append(job['type'])
    words.append(' !')

    words.append(' Location is ')
    words.append(job['address'])
    words.append(' !')


    # Say it!
    announcement = ' '.join(words)
    print(announcement)
    # Repeat announcement twice so they can be heard a bit clearly
    sayText(announcement)
    sayText("I repeat,")
    sayText(announcement)
    #sayText('S E S, Rollout!')

def monitor_jobs_api(isLiveSite=False):
    '''Connect to API and monitor for new jobs'''
    raise NotImplementedError('No API access information available for now')

def parse_jobs_table(browser):
    '''Parse the job register table and return a dict of jobs, with jobid as id'''
    # Refresh page required to ensure table is up to date
    browser.refresh()
    JobRegisterTable = browser.find_element_by_id("jobRegisterTable")
    # TODO
    # handle exception if table isnt loaded yet

    jobTable = BeautifulSoup(browser.page_source, "html.parser")
    jobRows = jobTable.find("table", id="jobRegisterTable").find("tbody").find_all("tr")

    jobs = {}
    for row in jobRows:
        cells = row.find_all("td")
        # Every second table row is 1 column wide and needs to be ignored
        if (len(cells) > 1):
            job = dict()
            job["id"] = cells[2].getText()
            job["received"] = cells[3].getText()
            job["priority"] = cells[4].getText()
            job["type"] = cells[5].getText()
            job["status"] = cells[6].getText()
            job["hq"] = cells[7].getText()
            job["parent"] = cells[8].getText()
            job["address"] = cells[9].getText()
            jobs[job["id"]] = job

    return jobs

def monitor_jobs_selenium(isLiveSite=False, isHeadless=False):
    '''Connect to web interface and parse jobs manually using Selenium'''

    # get credentials from system variables
    ses_login = os.environ.get("SES_LOGIN") or ''
    ses_pass = os.environ.get("SES_PASS") or ''

    if len(ses_login) < 1 or len(ses_pass) < 1:
        raise RuntimeError("No login credentials set. Set SES_LOGIN and SES_PASS environment variables")

    if isLiveSite:
        #baseurl = liveURL
        #loginurl = liveURL_login
        raise NotImplementedError ('Live site not implemented until feature complete') #TODO duh.
    else:
        baseurl = trainingURL
        loginurl = trainingURL_login

    opts = Options()
    if isHeadless:
        opts.set_headless()
        assert opts.headless  # Operating in headless mode

    browser = Firefox(options=opts)
    browser.get(baseurl + "/Jobs")
    
    if (browser.current_url.split("?")[0] == loginurl):
        # Login
        user_form = browser.find_element_by_id('username')
        user_form.send_keys(ses_login)
        pass_form = browser.find_element_by_id('password')
        pass_form.send_keys(ses_pass)
        pass_form.submit()

        
    # Check if login was successful
    # Are we still on the login screen?
    print(f"waiting {jobs_refresh_delay} seconds before checking login state")
    time.sleep(jobs_refresh_delay)
    if (browser.current_url.split("?")[0] == loginurl): 
         raise RuntimeError("Login error. Check username/password")
        
    # Try to get the initial list of jobs. We don't announce these.
    print(f"waiting for {initial_wait} seconds to allow website to load")
    time.sleep(initial_wait)

    known_jobs = {}
    # Comment out the parse function below to make us announce all initial jobs (for testing)
    # Else, this will get an initial list of jobs which will not be announced
    known_jobs = parse_jobs_table(browser)

    # Check for further additional jobs
    while True:
        print(f"waiting {jobs_refresh_delay} seconds")
        time.sleep(jobs_refresh_delay)

        # Hopefully the web page does not keep appending the jobs in the web page
        # so updated_job will not grow indefinitely
        updated_jobs = parse_jobs_table(browser)

        # Get new jobs by finding the diff between two sets, see https://stackoverflow.com/a/30986796
        new_job_ids = set(updated_jobs.keys()) - set(known_jobs.keys())

        # We don't need the old jobs anymore, replace with collection of new jobs
        known_jobs = updated_jobs

        # Announce all new jobs
        for job in new_job_ids:
            announceJob(known_jobs[job])


def parseinput():
    helptext = 'Script that parses SES alerts site and announces it through the station'
    parser = argparse.ArgumentParser(description=helptext)

    # Select between training and live site. Argument mandatory;
    # we don't want default to live site (us developers should not mess with live system by accident)
    # but we also don't want SES guys to accidentally set this monitor to training site (which can cause people to die)
    target_livesite = parser.add_mutually_exclusive_group(required=True)
    target_livesite.add_argument('--live', action='store_true', help='Parse the live SES site')
    target_livesite.add_argument('--training', action='store_true', help='Parse the training SES site')
    
    # Use headless browser
    parser.add_argument('--headless', action='store_true', default=False, help='Use headless browser instead of popping a Firefox window')

    return parser.parse_args()


if __name__ == "__main__":
    """ This is executed when run from the command line """
    args = parseinput()
    if args.live:
        livesite = True
    if args.training:
        livesite = False

    # allows the operator to verify the speaker is working
    print('Saying speaker test...')
    #sayText('This is the S E S Rollout speaker test message!')

    # List available serial ports
    list_ports()
    
    #monitor_jobs_api(livesite)
    monitor_jobs_selenium(livesite, args.headless)


