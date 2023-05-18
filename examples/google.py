import selenium.webdriver
import selenium.webdriver.common.keys
import time

import selenium_soup

browser = selenium_soup.Browser(selenium.webdriver.Firefox())

browser.navigateTo('https://google.com')
body = browser.body()
searchBox = body.selectAll('textarea')[0]
searchBoxDriver = searchBox.driver()
searchBoxDriver.click()
searchBoxDriver.send_keys('pears')
searchBoxDriver.send_keys(selenium.webdriver.common.keys.Keys.RETURN)

time.sleep(0.5)
browser.waitUntilSelector('div#search')
body = browser.body()
searchResults = body.selectUnique('div#search')
resultH3s = searchResults.selectAll('h3', maxElements=100)
for resultH3 in resultH3s:
  result_title = resultH3.tree().text
  url = resultH3.parent().tree()['href']
  print(result_title)
  print(url)
