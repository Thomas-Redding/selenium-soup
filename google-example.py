
import selenium.webdriver
import selenium.webdriver.common.keys
import time

import shared

browser = shared.Browser(selenium.webdriver.Firefox())

browser.navigateTo('https://google.com')
body = browser.body()
searchBox = body.selectUnique("input[type='text']")
searchBoxDriver = searchBox.driver()
searchBoxDriver.click()
searchBoxDriver.send_keys('pears')
searchBoxDriver.send_keys(selenium.webdriver.common.keys.Keys.RETURN)

for i in range(10):
  time.sleep(0.5)
  browser.waitUntilSelector('div#search')
  body = browser.body()
  searchResults = body.selectUnique('div#search')
  resultH3s = searchResults.selectAll('h3', maxElements=100)
  for resultH3 in resultH3s:
    resultTitle = resultH3.tree().text
    aTag = resultH3.parent().tree().a
    if not aTag: continue # section heading (e.g. "People also ask") rather than search result
    resultURL = resultH3.parent().tree().a['href']
    print(resultTitle, resultURL)
  nextButton = body.selectUnique('a#pnnext')
  nextButton.click()
