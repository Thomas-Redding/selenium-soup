# Selenium Soup

This is a small module that basically just adds some glue to [Selenium](https://selenium-python.readthedocs.io/) and [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) to make web scraping easier.


## Build & Install

```bash
cd ..
python3 -m pip install selenium-soup/
# Veryify at /usr/local/lib/python3.11/site-packages
```

or

```bash
cd ..
pip3 install selenium-soup/
# Veryify at /usr/local/lib/python3.11/site-packages
```

## Example Usage

```python
import selenium_soup

browser = selenium_soup.Browser(selenium.webdriver.Chrome())
# browser = selenium_soup.Browser(selenium.webdriver.Firefox())
browser.navigateTo('https://www.foobar.com')
input('Sign in if necessary. Then hit ENTER.')

for username in ['alice', 'bob', 'carol', 'dan', 'eve']:
  browser.navigateTo('https://www.foobar.com/profile/%s' % username)
  browser.body().selectUnique('button.expand-profile').click()
  user_score = browser.body().selectUnique('span.score-label').js('return self.innerHTML;').strip()
  friend_links = browser.body().selectAll('table.friend-table tr a')
  friend_urls = list(map(lambda link: link.tree()['href'], friend_links))
  print(username, user_score, friend_urls)
```

### Persistent User Data (e.g. cookies)

Suppose your scraping requires you to sign into a website, and this is annoying to do every time (or causes you to get blocked). Just replace

```python
browser = selenium_soup.Browser(selenium.webdriver.Chrome())
```

with

```python
import os
home_dir = os.path.expanduser('~')
browser = selenium_soup.Browser.persistentChromeBrowser(
  home_dir + '/Downloads/chromedriver_mac64/chromedriver', 
  'Chrome', 'tester'
)
```

and then download `chromedriver` from either [here](https://chromedriver.chromium.org/downloads) or [here](https://googlechromelabs.github.io/chrome-for-testing/).
