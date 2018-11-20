"""
SES Rollout
"""

__author__ = "mgf897, ssfivy"
__version__ = "0.1.0"
__license__ = "CC SA"

import os
import time
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup

baseURL = "https://trainbeacon.ses.nsw.gov.au"
loginURL = "https://identitytrain.ses.nsw.gov.au/core/login"
jobsURL = baseURL + "/Jobs"
delay = 10

def annouceJob(job):
    print(job)


def main():
    # get credentials from system variables
    ses_login = os.environ.get("SES_LOGIN")
    ses_pass = os.environ.get("SES_PASS")

    if ses_login and ses_pass:
        opts = Options()
        #opts.set_headless()
        #assert opts.headless  # Operating in headless mode
        browser = Firefox(options=opts)

        browser.get(jobsURL)
        page_url = browser.current_url

        if (browser.current_url.split("?")[0] == loginURL):
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
            print(f"waiting {delay} seconds")
            time.sleep(delay)

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

    else:
        print("No login credentials set. Set SES_LOGIN and SES_PASS environment variables")


if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()


