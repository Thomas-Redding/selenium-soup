
import bs4
import os

import selenium.webdriver.support.expected_conditions
import selenium.webdriver.support.ui
import selenium.webdriver.common.by
import time
import urllib.request
import urllib.parse

########## bs4 + selenium + urllib ##########

# This library creates a set of HTMLElement objects.
# These objects maintain a 1:1 mapping between the following:
#   * bs4 ("beautiful soup")'s element objects
#   * Selenium's WebElement objects
#   * JavaScript's elements

### If you have an HTMLElement object (foo), you can get the associated bs4 and selenium objects using:
# foo.tree(): bs4.BeautifulSoup
# foo.driver(): selenium.webdriver.remote.webelement.WebElement

### Here are some other useful methods:
# parent(): HTMLElement
# updateTree()
# selectOne(cssSelector: string): HTMLElement
# selectAll(cssSelector: string, maxElements=100: integer): list<HTMLElement>
# selectUnique(cssSelector: string): HTMLElement
# xpath(xpathExpression: string, resultType: string): list<HTMLElement>
# click()
# js(javascript: string): any

class HTMLElement:
  def __init__(self, browser, html, reddingID):
    self._browser = browser
    self._tree = bs4.BeautifulSoup(html, 'html.parser')
    if self._tree.name == '[document]':
      # Consider `== bs4.element.Tag` instead
      tmp = list(filter(lambda x: type(x) != bs4.element.NavigableString, self._tree.children))
      assert len(tmp) == 1
      self._tree = tmp[0]
    else:
      print('QQ', self._tree.name)
    self._reddingID = reddingID
    self._driverElement = None

  def tree(self):
    return self._tree

  def driver(self):
    if self._driverElement == None:
      driver = self._browser.webDriver()
      print(driver)
      self._driverElement = driver.find_element(selenium.webdriver.common.by.By.CSS_SELECTOR, '[redding_id="%i"]' % self._reddingID)
    return self._driverElement

  def parent(self):
    self._browser._reddingIDCounter += 1
    results = self._browser._browser.execute_script("""
      let mes = document.querySelectorAll('[redding_id="%i"]');
      if (mes.length !== 1) {
        return -1;
      }
      let me = mes[0];
      let match = me.parentElement
      if (match == undefined) {
        return null;
      }
      let reddingID = match.getAttribute("redding_id");
      if (reddingID == null) {
        reddingID = %i;
        match.setAttribute("redding_id", reddingID);
      }
      return [match.outerHTML, parseInt(reddingID)];
    """ % (self._reddingID, self._browser._reddingIDCounter))
    if results == -1:
      raise Exception("Element was removed")
    if results == None:
      return None
    html, reddingID = results
    return HTMLElement(self._browser, html, reddingID)

  def updateTree(self):
    results = self._browser._browser.execute_script("""
      let mes = document.querySelectorAll('[redding_id="%i"]');
      if (mes.length !== 1) {
        return -1;
      }
      return mes[0].outerHTML;
    """ % self._reddingID)
    if results == -1:
      raise Exception("Element was removed")
    self._tree = bs4.BeautifulSoup(results, 'html.parser')

  def selectOne(self, cssSelector):
    cssSelector = self.escapeCssSelector(cssSelector)
    self._browser._reddingIDCounter += 1
    results = self._browser._browser.execute_script("""
      let mes = document.querySelectorAll('[redding_id="%i"]');
      if (mes.length !== 1) {
        throw -1
      }
      let me = mes[0];
      let match = me.querySelector("%s");
      if (match == undefined) {
        return null;
      }
      let reddingID = match.getAttribute("redding_id");
      if (reddingID == null) {
        reddingID = %i;
        match.setAttribute("redding_id", reddingID);
      }
      return [match.outerHTML, parseInt(reddingID)];
    """ % (self._reddingID, cssSelector, self._browser._reddingIDCounter))
    if results == -1:
      raise Exception("Element was removed")
    if results == None:
      return None
    html, reddingID = results
    return HTMLElement(self._browser, html, reddingID)

  def selectAll(self, cssSelector, maxElements=100):
    cssSelector = self.escapeCssSelector(cssSelector)
    self._browser._reddingIDCounter += 1
    results = self._browser._browser.execute_script("""
      let mes = document.querySelectorAll('[redding_id="%i"]');
      if (mes.length !== 1) {
        return -1;
      }
      let me = mes[0];
      let matches = me.querySelectorAll("%s");
      let nextReddingID = %i;
      let maxElements = %i;
      if (matches.length > maxElements) {
        return matches.length;
      }
      let rtn = [];
      for (let match of matches) {
        let reddingID = match.getAttribute("redding_id");
        if (reddingID == null) {
          reddingID = nextReddingID;
          match.setAttribute("redding_id", reddingID);
          ++nextReddingID;
        }
        rtn.push([match.outerHTML, parseInt(reddingID)]);
      }
      return rtn;
    """ % (self._reddingID, cssSelector, self._browser._reddingIDCounter, maxElements))
    if type(results) == int:
      if results < 0:
        raise Exception("Element was removed")
      else:
        raise Exception("Too many results (%i > %i) for selector (%s)" % (results, maxElements, cssSelector))
    self._browser._reddingIDCounter += len(results)
    rtn = []
    for result in results:
      html, reddingID = result
      rtn.append(HTMLElement(self._browser, html, reddingID))
    return rtn

  def selectUnique(self, cssSelector):
    cssSelector = self.escapeCssSelector(cssSelector)
    self._browser._reddingIDCounter += 1
    results = self._browser._browser.execute_script("""
      let mes = document.querySelectorAll('[redding_id="%i"]');
      if (mes.length !== 1) {
        return -1;
      }
      let me = mes[0];
      let matches = me.querySelectorAll("%s");
      if (matches.length !== 1) {
        return matches.length;
      }
      let match = matches[0];
      let reddingID = match.getAttribute("redding_id");
      if (reddingID == null) {
        reddingID = %i;
        match.setAttribute("redding_id", reddingID);
      }
      return [match.outerHTML, parseInt(reddingID)];
    """ % (self._reddingID, cssSelector, self._browser._reddingIDCounter))
    if type(results) == int:
      if results < 0:
        raise Exception("Element was removed")
      else:
        raise Exception("Wrong number (%i) of elements found for selector (%s)" % (results, cssSelector))
    html, reddingID = results
    return HTMLElement(self._browser, html, reddingID)

  # https://developer.mozilla.org/en-US/docs/Web/XPath/Introduction_to_using_XPath_in_JavaScript
  # https://developer.mozilla.org/en-US/docs/Web/API/XPathResult
  def xpath(self, xpathExpression, resultType):
    assert False, 'xpath() is not yet implemented (TODO)'
    self._browser._reddingIDCounter += 1
    assert resultType in [
      # 'ANY_TYPE',
      'ANY_UNORDERED_NODE_TYPE',
      'BOOLEAN_TYPE',
      'FIRST_ORDERED_NODE_TYPE',
      'NUMBER_TYPE',
      'ORDERED_NODE_ITERATOR_TYPE',
      'ORDERED_NODE_SNAPSHOT_TYPE',
      'STRING_TYPE',
      'UNORDERED_NODE_ITERATOR_TYPE',
      'UNORDERED_NODE_SNAPSHOT_TYPE'
    ]
    escapedXpathExpression = xpathExpression.replace('"', '\\"')
    results = self._browser._browser.execute_script("""
      let mes = document.querySelectorAll('[redding_id="%i"]');
      if (mes.length !== 1) {
        return null;
      }
      let me = mes[0];
      let xpathResult = document.evaluate(\"%s\", me, null, XPathResult.%s);
      if (xpathResult.resultType === 0) { // ANY_TYPE
        // TODO
      } else if (xpathResult.resultType === 1) { // NUMBER_TYPE
        return xpathResult.numberValue;
      } else if (xpathResult.resultType === 2) { // STRING_TYPE
        return xpathResult.stringValue;
      } else if (xpathResult.resultType === 3) { // BOOLEAN_TYPE
        return xpathResult.booleanValue;
      } else if (xpathResult.resultType === 8 || xpathResult.resultType === 9) {
        // ANY_UNORDERED_NODE_TYPE
        // FIRST_ORDERED_NODE_TYPE
        return xpathResult.singleNodeValue;
      } else {
        // ORDERED_NODE_ITERATOR_TYPE
        // ORDERED_NODE_SNAPSHOT_TYPE
        // UNORDERED_NODE_ITERATOR_TYPE
        // UNORDERED_NODE_SNAPSHOT_TYPE
        let rtn = [];
        let node = xpathResult.iterateNext();
        let reddingIDCounter = %i;
        while (node) {
          let reddingID = node.getAttribute("redding_id");
          if (reddingID == null) {
            reddingID = reddingIDCounter;
            ++reddingIDCounter;
            node.setAttribute("redding_id", reddingID);
          }
          rtn.push([node.outterHTML, parseInt(reddingID)]);
          node = xpathResult.iterateNext();
        }
        return rtn;
      }
    """ % (self._reddingID, escapedXpathExpression, resultType, self._browser._reddingIDCounter))
    print(results)
    if results == None:
      raise Exception("Tag (%s) with text (%s) not found" % (tagName, escapedText))
    if resultType in ['ANY_UNORDERED_NODE_TYPE', 'BOOLEAN_TYPE', 'FIRST_ORDERED_NODE_TYPE', 'NUMBER_TYPE', 'STRING_TYPE']:
      self._browser._reddingIDCounter += 1
      return results
    self._browser._reddingIDCounter += len(results)
    rtn = []
    for result in results:
      html, reddingID = result
      rtn.append(HTMLElement(self, html, reddingID))
    return rtn

  def click(self):
    results = self._browser._browser.execute_script("""
      let mes = document.querySelectorAll('[redding_id="%i"]');
      if (mes.length !== 1) {
        return -1;
      }
      let me = mes[0];
      me.click();
    """ % (self._reddingID))
    if results == -1:
      raise Exception("Element was removed")

  def escapeCssSelector(self, cssSelector):
    return cssSelector.replace('"', '\\"')

  # Execute the given javascript after setting a `self` variable to this element.
  def js(self, javascript):
    prefix = """
      let self = document.querySelectorAll('[redding_id="%i"]')[0];
    """ % self._reddingID
    return self._browser.js(prefix + javascript)

# navigateTo(url: string, timeOut=10)
# waitUntilSelector(cssSelector: string, timeOut=5)
# body(force=False: boolean): HTMLElement
# webDriver(): selenium.webdriver.firefox.webdriver.WebDriver
# js(javascript: string): any
# download(url: string, path: string)
# parseURL(url: string): ParseResult
class Browser:
  def __init__(self, browser):
    self._browser = browser
    self._reddingIDCounter = 0
    self._body = None
    self._lastUserAgent = None

  def navigateTo(self, url, timeOut=10):
    self._reddingIDCounter = 0
    self._body = None
    self._browser.get(url)
    self.waitForPageToLoad(timeOut)

  def waitForPageToLoad(self, timeOut):
    # Wait for the page to load.
    startTime = time.time()
    while True:
      if time.time() - startTime > timeOut:
        assert False, "Took more than 10 seconds to load the page"
      time.sleep(0.1)
      page_state = self._browser.execute_script('return document.readyState;')
      if page_state == 'complete':
        break
    time.sleep(0.5) # just in case

  def waitUntilSelector(self, cssSelector, timeOut=5):
    return selenium.webdriver.support.ui.WebDriverWait(self._browser, timeOut).until(selenium.webdriver.support.expected_conditions.presence_of_element_located((selenium.webdriver.common.by.By.CSS_SELECTOR, cssSelector)))

  def body(self, force=False):
    # If the body is cached and hasn't been replaced by a page-navigations, just return it.
    if force:
      self._body = None
    if self._body:
      reddingID = self._browser.execute_script("""
        return document.body.getAttribute("redding_id");
      """)
      if reddingID:
        return self._body
    self._reddingIDCounter += 1
    results = self._browser.execute_script("""
      let reddingID = document.body.getAttribute("redding_id");
      if (reddingID == null) {
        reddingID = %i;
        document.body.setAttribute("redding_id", reddingID);
      }
      return [document.body.outerHTML, parseInt(reddingID)]
    """ % self._reddingIDCounter)
    self._body = HTMLElement(self, results[0], results[1])
    return self._body

  # Support ad-hoc selenium methods
  def webDriver(self):
    return self._browser

  def js(self, javascript):
    return self._browser.execute_script(javascript)

  def download(self, url, path):
    # TODO: Support cookies
    userAgent = driver.execute_script("return navigator.userAgent;")
    if userAgent != self._lastUserAgent:
      headers = {'User-Agent': userAgent}
      opener = urllib.request.build_opener()
      opener.addheaders = [('User-agent', HEADERS['User-Agent'])]
      urllib.request.install_opener(opener)
    urllib.request.urlretrieve(url, path)

  def parseURL(self, url):
    return urllib.parse.urlparse(url)










########## utilities ##########

def say(s):
  os.system("say %s" % s)

def unique(iterator):
  counter = 0
  rtn = None
  for x in iterator:
    if counter != 0:
      assert False
    rtn = x
    counter += 1
  assert counter == 1
  return rtn

def maybeOne(iterator):
  counter = 0
  rtn = None
  for x in iterator:
    if counter != 0:
      assert False
    rtn = x
    counter += 1
  return rtn

def ith(iterator, index):
  assert type(index) == int
  assert index >= 0
  counter = 0
  for it in iterator:
    if counter == index:
      return it
    counter += 1
  raise Exception()

def length(iterator):
  counter = 0
  for it in iterator:
    counter += 1
  return counter

def empty(iterator):
  for x in iterator:
    return False
  return True
