
import selenium.webdriver
import selenium.webdriver.common.keys
import time

import shared

argName = 'Thomas Kurian'

# Open up Chrome browser with persistent data.
# For this to work, you must first quit Google Chrome.
kDriverPath = '/Users/tfr/proj/data/scraped/scripts/chromedriver'
kUserDataPath = '/Users/tfr/Library/Application Support/Google/Chrome'
options = selenium.webdriver.chrome.options.Options()
options.add_argument("user-data-dir=%s" % kUserDataPath)
options.add_argument('profile-directory=tester')
c = selenium.webdriver.Chrome(executable_path=kDriverPath, chrome_options=options)
browser = shared.Browser(c)

input('If this is your first time user the "tester" profile, navigate to and sign into linkedin.com. Then hit ENTER.')

# Navigate to linkedin.com.
browser.navigateTo('https://www.linkedin.com/')
body = browser.body()

# Search for the person's name.
body.selectUnique('input[aria-label="Search"]').driver().send_keys(argName)
body.selectUnique('input[aria-label="Search"]').driver().send_keys(selenium.webdriver.common.keys.Keys.RETURN)
time.sleep(2)
body.updateTree()

# Limit search to people.
searchFilters = body.selectUnique('nav[aria-label="Search filters"')
searchFilterButtons = searchFilters.selectAll('button')
assert searchFilterButtons[0].tree().text == '\n  \n  People\n\n'
searchFilterButtons[0].click()
time.sleep(1)

# Limit search to Google employees.
# The `searchFilters` element is removed, so updateTree() won't work.
# We have to fetch it again:
searchFilters = body.selectUnique('nav[aria-label="Search filters"')
currentCompanyFilterButton = searchFilters.selectUnique('button[aria-label="Current company filter. Clicking this button displays all Current company filter options."]')
currentCompanyFilterButton.click()
time.sleep(1)
body.updateTree()
companySearchBox = body.selectUnique('input[placeholder="Add a company"]')
companySearchBox.driver().send_keys("Google")
time.sleep(2)
instantResultsContainer = body.selectUnique('div.basic-typeahead__triggered-content')
resultContainerID = instantResultsContainer.tree().attrs['id']
assert resultContainerID.startswith('triggered-expanded-ember')
searchID = resultContainerID[len('triggered-expanded-ember'):]
instantResults = instantResultsContainer.selectAll('span.search-typeahead-v2__hit-text')
for instantResult in instantResults:
  if instantResult.tree().text.strip() == 'Google':
    break

assert instantResult.tree().text.strip() == 'Google'
instantResult.click()
time.sleep(1)
body.updateTree()
buttons = body.selectAll('button[aria-label="Apply current filter to show results"]')
buttons[2].click()
time.sleep(1)

# Assert there is only one result.
numResultsString = body.selectUnique('h2.pb2').tree().text.strip()
assert numResultsString == '1 result'

results = body.selectAll('li.reusable-search__result-container')
assert len(results) == 1

# Click the result to open the person's profile.
results[0].selectUnique('a > span').click()

# Scrape relevant data.

def getSectionForHeader(header):
  tmp = header.parent()
  while tmp:
    if tmp.tree().name == 'section':
      return tmp
    tmp = tmp.parent()
  return None

h2s = body.selectAll('h2')
experienceSection = None
educationSection = None
for h2 in h2s:
  s = h2.tree().text.strip()
  if s == 'ExperienceExperience':
    experienceSection = getSectionForHeader(h2)
  elif s == 'EducationEducation':
    educationSection = getSectionForHeader(h2)

# TODO: Extract text from HTML



