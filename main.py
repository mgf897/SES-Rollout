#!/usr/bin/env python3

"""
SES Rollout
"""

__author__ = "mgf897, ssfivy"
__version__ = "0.1.0"
__license__ = "CC SA"

import argparse
import sys
import os
import time
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup

trainingURL = "https://trainbeacon.ses.nsw.gov.au"
trainingURL_login = "https://identitytrain.ses.nsw.gov.au/core/login"

liveURL = "" # TODO: Fill this infromation
liveURL_login = "" # TODO: Fill this information

jobs_refresh_delay = 10

# version number check: Require 3.6
if sys.version_info < (3, 6) :
    raise NotImplementedError('This script requires Python version 3.6 or later')

def annouceJob(job):
    print(job)

def monitor_jobs_api(isLiveSite=False):
    '''Connect to API and monitor for new jobs'''
    raise NotImplementedError('No API access information available for now')

def monitor_jobs_selenium(isLiveSite=False, isHeadless=False):
    '''Connect to web interface and parse jobs manually using Selenium'''

    # get credentials from system variables
    ses_login = os.environ.get("SES_LOGIN")
    ses_pass = os.environ.get("SES_PASS")

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
    page_url = browser.current_url

    if (browser.current_url.split("?")[0] == loginurl):
        # Login
        user_form = browser.find_element_by_id('username')
        user_form.send_keys(ses_login)
        pass_form = browser.find_element_by_id('password')
        pass_form.send_keys(ses_pass)
        pass_form.submit()

    else:
        # Aready logged in
        pass

    # TODO
    # Browser should redirect to jobs page. Make sure we are on the Jobs page. If not, request it

    jobRegisterTable = object()
    knownJobIds = list()

    while True:
        print(f"waiting {jobs_refresh_delay} seconds")
        time.sleep(jobs_refresh_delay)

        newJobRegisterTable = browser.find_element_by_id("jobRegisterTable")

        # TODO
        # handle exception if table isnt loaded yet

        # Quickly compare raw tables before parsing
        if (jobRegisterTable != newJobRegisterTable):
            print("Update to job table")
            jobRegisterTable = newJobRegisterTable

            jobTable = BeautifulSoup(browser.page_source, "html.parser")
            jobRows = jobTable.find("table", id="jobRegisterTable").find("tbody").find_all("tr")
            for jobRow in jobRows:
                cells = jobRow.find_all("td")
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

                    if job["id"] not in knownJobIds:
                        # New job
                        knownJobIds.append(job["id"])
                        annouceJob(job)

        else:
            print("No new jobs")

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

    try:
        monitor_jobs_api(livesite)
    except:
        monitor_jobs_selenium(livesite, args.headless)


