
import base64
import bs4
import json
import os
import pyautogui # pip3 install pyautogui
import re
import selenium.webdriver.support.expected_conditions
import selenium.webdriver.support.ui
import selenium.webdriver.common.by
import seleniumwire.utils
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
# contents(): str
# parent(): HTMLElement
# updateTree()
# selectOne(cssSelector: str): HTMLElement
# selectAll(cssSelector: str, maxElements=100: integer): list<HTMLElement>
# selectUnique(cssSelector: str): HTMLElement
# xpath(xpathExpression: str, resultType: str): list<HTMLElement>
# click()
# js(javascript: str): any

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

  def contents(self):
    return self._tree.encode_contents().decode('utf-8')

  def driver(self):
    if self._driverElement == None:
      driver = self._browser.driver()
      self._driverElement = driver.find_element(selenium.webdriver.common.by.By.CSS_SELECTOR, '[redding_id="%i"]' % self._reddingID)
    return self._driverElement

  def seleniumElementForXPath(self, xpathExpression):
    return self.driver().find_element(selenium.webdriver.common.by.By.XPATH, xpathExpression)

  def seleniumElementsForXPath(self, xpathExpression):
    return self.driver().find_elements(selenium.webdriver.common.by.By.XPATH, xpathExpression)

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

  def children(self):
    self._browser._reddingIDCounter += 1
    results = self._browser._browser.execute_script("""
      let mes = document.querySelectorAll('[redding_id="%i"]');
      if (mes.length !== 1) {
        return -1;
      }
      let me = mes[0];
      let nextReddingID = %i;
      let rtn = [];
      for (let i = 0; i < me.children.length; ++i) {
        let reddingID = me.children[i].getAttribute("redding_id");
        if (reddingID == null) {
          me.children[i].setAttribute("redding_id", nextReddingID);
          ++nextReddingID;
        }
        rtn.push([me.children[i].outerHTML, parseInt(me.children[i].getAttribute("redding_id"))]);
      }
      return rtn;
    """ % (self._reddingID, self._browser._reddingIDCounter))
    if type(results) == int:
      if results < 0:
        raise Exception("Element was removed")
      else:
        raise Exception("Unknown issue")
    self._browser._reddingIDCounter += len(results)
    rtn = []
    for result in results:
      html, reddingID = result
      rtn.append(HTMLElement(self._browser, html, reddingID))
    return rtn

  def childNodes(self):
    self._browser._reddingIDCounter += 1
    results = self._browser._browser.execute_script("""
      let mes = document.querySelectorAll('[redding_id="%i"]');
      if (mes.length !== 1) {
        return -1;
      }
      let me = mes[0];
      let nextReddingID = %i;
      let rtn = [];
      for (let i = 0; i < me.childNodes.length; ++i) {
        if (me.childNodes[i].tagName === undefined) {
          rtn.push([me.childNodes[i].textContent, null]);
        } else {
          let reddingID = me.childNodes[i].getAttribute("redding_id");
          if (reddingID == null) {
            me.childNodes[i].setAttribute("redding_id", nextReddingID);
            ++nextReddingID;
          }
          rtn.push([me.childNodes[i].outerHTML, parseInt(me.childNodes[i].getAttribute("redding_id"))]);
        }
      }
      return rtn;
    """ % (self._reddingID, self._browser._reddingIDCounter))
    if type(results) == int:
      if results < 0:
        raise Exception("Element was removed")
      else:
        raise Exception("Unknown issue")
    self._browser._reddingIDCounter += len(results)
    rtn = []
    for result in results:
      html, reddingID = result
      print(reddingID, html)
      if reddingID is None:
        rtn.append(html)
      else:
        rtn.append(HTMLElement(self._browser, html, reddingID))
    return rtn

  def selectOne(self, cssSelector):
    cssSelector = HTMLElement.escapeCssSelector(cssSelector)
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
    cssSelector = HTMLElement.escapeCssSelector(cssSelector)
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
    cssSelector = HTMLElement.escapeCssSelector(cssSelector)
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

  def click(self, useDriver=True):
    if useDriver:
      self.driver().click()
    else:
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

  @classmethod
  def escapeCssSelector(self, cssSelector):
    return cssSelector.replace('"', '\\"')

  # Execute the given javascript after setting a `self` variable to this element.
  def js(self, javascript):
    prefix = """
      let self = document.querySelectorAll('[redding_id="%i"]')[0];
    """ % self._reddingID
    return self._browser.js(prefix + javascript)

  def saveImageFromRAMAsPng(self, path):
    assert self._tree.name == 'img'
    # https://stackoverflow.com/a/61061867
    script = """
      var c = document.createElement('canvas');
      var ctx = c.getContext('2d');
      c.height = self.naturalHeight;
      c.width = self.naturalWidth;
      ctx.drawImage(self, 0, 0, self.naturalWidth, self.naturalHeight);
      var base64String = c.toDataURL();
      return base64String;
    """
    base64String = self.js(script)
    assert base64String.startswith('data:image/png;base64,')
    imageData = base64.b64decode(base64String[len('data:image/png;base64,'):])
    with open(path, "wb") as f:
      f.write(imageData)





# INSTANCE METHODS:
#   navigateTo(url: str, timeOut=10)
#   waitForPageToLoad(timeOut=10)
#   withFor(timeOut: float, fn: (browser) => {})
#   waitForSelector(cssSelector: str, timeOut=10)
#   body(force=False: boolean): HTMLElement
#   driver(): selenium.webdriver.firefox.webdriver.WebDriver
#   selectOne(cssSelector: str): HTMLElement
#   selectAll(cssSelector: str, maxElements=100: integer): list<HTMLElement>
#   selectUnique(cssSelector: str): HTMLElement
#   js(javascript: str): any
#   download(url: str, path: str)
#   absolutifyUrl(potentially_relative_url: str): str
#   focus()
#   save_system(path_relative_to_save_dialog: str)
#   save_beta(path: str)
# CLASS METHODS
#   absolutifyUrlRelativetoPage(potentially_relative_url: str, page_url: str): str
#   download_basic(url: str, path: str, userAgent: str)
#   persistentChromeBrowser(driverPath: str, userDataPath: str, profileDirectory: str): Browser
#   parseURL(url: str): str
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
    self.withFor(timeOut, lambda browser: browser.js('return document.readyState;') == 'complete')

  def withFor(self, timeOut, fn):
    # Wait for the page to load.
    time.sleep(0.1)
    startTime = time.time()
    while True:
      if time.time() - startTime > timeOut:
        assert False, "Took more than %i seconds to load the page" % timeOut
      time.sleep(0.1)
      if fn(self): break
    time.sleep(0.5) # just in case

  def waitForSelector(self, cssSelector, timeOut=10):
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
  def driver(self):
    return self._browser

  # deprecated
  def webDriver(self):
    return self._browser

  def js(self, javascript):
    return self._browser.execute_script(javascript)

  def download(self, url, path):
    # TODO: Support cookies
    userAgent = self.driver().execute_script("return navigator.userAgent;")
    url = self.absolutifyUrl(url)
    Browser.download_basic(url, path, userAgent)

  def seleniumElementForXPath(self, xpathExpression):
    return self.driver().find_element(selenium.webdriver.common.by.By.XPATH, xpathExpression)

  def seleniumElementsForXPath(self, xpathExpression):
    return self.driver().find_elements(selenium.webdriver.common.by.By.XPATH, xpathExpression)

  def clearBrowserData(self):
    self._browser.execute_cdp_cmd('Storage.clearDataForOrigin', {
        "origin": '*',
        "storageTypes": 'all',
    })

  def selectOne(self, cssSelector):
    cssSelector = HTMLElement.escapeCssSelector(cssSelector)
    self._reddingIDCounter += 1
    results = self._browser.execute_script("""
      let match = document.querySelector("%s");
      if (match == undefined) {
        return null;
      }
      let reddingID = match.getAttribute("redding_id");
      if (reddingID == null) {
        reddingID = %i;
        match.setAttribute("redding_id", reddingID);
      }
      return [match.outerHTML, parseInt(reddingID)];
    """ % (cssSelector, self._reddingIDCounter))
    if results == -1:
      raise Exception("Element was removed")
    if results == None:
      return None
    html, reddingID = results
    return HTMLElement(self, html, reddingID)

  def selectAll(self, cssSelector, maxElements=100):
    cssSelector = HTMLElement.escapeCssSelector(cssSelector)
    self._reddingIDCounter += 1
    results = self._browser.execute_script("""
      document.querySelectorAll("%s");
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
    """ % (cssSelector, self._reddingIDCounter, maxElements))
    if type(results) == int:
      if results < 0:
        raise Exception("Element was removed")
      else:
        raise Exception("Too many results (%i > %i) for selector (%s)" % (results, maxElements, cssSelector))
    self._reddingIDCounter += len(results)
    rtn = []
    for result in results:
      html, reddingID = result
      rtn.append(HTMLElement(self, html, reddingID))
    return rtn

  def selectUnique(self, cssSelector):
    cssSelector = HTMLElement.escapeCssSelector(cssSelector)
    self._reddingIDCounter += 1
    results = self._browser.execute_script("""
      let matches = document.querySelectorAll("%s");
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
    """ % (cssSelector, self._reddingIDCounter))
    if type(results) == int:
      if results < 0:
        raise Exception("Element was removed")
      else:
        raise Exception("Wrong number (%i) of elements found for selector (%s)" % (results, cssSelector))
    html, reddingID = results
    return HTMLElement(self, html, reddingID)

  @classmethod
  # 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
  def download_basic(cls, url, path, userAgent=None):
    if userAgent:
      headers = {'User-Agent': userAgent}
      opener = urllib.request.build_opener()
      opener.addheaders = [('User-agent', userAgent)]
      urllib.request.install_opener(opener)
    urllib.request.urlretrieve(url, path)

  # Open up Chrome browser with persistent user data.
  # For this to work, you must first quit Google Chrome.
  # @param driverPath - driver download from https://chromedriver.chromium.org/downloads
  #                     example: "chromedriver_mac64/chromedriver"
  # @param userDataPath - '~/Library/Application Support/Google/Chrome'
  # @param profileDirectory - 'tester'
  # TODO: Investigate using 'Default' as `profileDirectory`.
  @classmethod
  def persistentChromeBrowser(cls, driverPath, userDataPath, profileDirectory):
    options = selenium.webdriver.chrome.options.Options()
    options.add_argument("user-data-dir=%s" % userDataPath)
    options.add_argument('profile-directory=%s' % profileDirectory)
    c = selenium.webdriver.Chrome(executable_path=driverPath, chrome_options=options)
    return Browser(c)

  @classmethod
  def parseURL(cls, url):
    return urllib.parse.urlparse(url)

  def absolutifyUrl(self, potentially_relative_url):
    page_url = self.js('return window.location.href;')
    return Browser.absolutifyUrlRelativetoPage(potentially_relative_url, page_url)

  @classmethod
  def absolutifyUrlRelativetoPage(cls, potentially_relative_url, page_url):
    url = potentially_relative_url
    if url.startswith('http://') or url.startswith('https://'):
      return url
    page_url_info = urllib.parse.urlparse(page_url)
    if url.startswith('//'):
      return page_url_info.scheme + ':' + url
    if url.startswith('/'):
      # TODO: `page_url.hostname` or `page_url.netloc`
      return page_url_info.scheme + '://' + page_url_info.hostname + url
    page_dir = os.path.split(page_url_info.path)[0]
    if url.startswith('./'):
      url = url[2:]
    while url.startswith('../'):
      page_dir = '/'.join(page_dir.split('/')[:-1])
      url = url[3:]
    if page_dir == '/':
      page_dir = ''
    return page_url_info.scheme + '://' + page_url_info.hostname + page_dir + '/' + url

  def focus(self):
    rect = self._browser.get_window_rect()
    self._browser.minimize_window()
    self._browser.maximize_window()
    self._browser.set_window_rect(rect['x'], rect['y'], rect['width'], rect['height'])

  # https://stackoverflow.com/a/53966809
  def save_system(self, path_relative_to_save_dialog):
    pyautogui.hotkey('command', 's')
    # First time will likely prompt user for OS permission.
    time.sleep(1)
    pyautogui.typewrite(path_relative_to_save_dialog)
    pyautogui.hotkey('enter')

  def save_page(self, path):
    pd = PageDownloader(self, path)





########## PageDownloader ##########

class PageDownloader:
  def __init__(self, browser, root):
    assert root.endswith('/'), 'root ("%s") must end in a slash' % root
    os.mkdir(root)
    self._root = root
    self._browser = browser
    self._srcs = {} # absolute web browser URL -> local filesystem URL
    html = self._browser.driver().page_source
    dom = bs4.BeautifulSoup(html)
    self._saveImagesInRam()
    self._downloadSrcsAndHrefs(dom)
    with open(self._root + 'index.html', 'w') as f:
      f.write('<!DOCTYPE html>\n' + dom.decode())
    self.recursively_download_stylesheets()

  def _iterate(self, tag, fn):
    fn(tag)
    if tag.name is not None:
      for child in tag.children:
        self._iterate(child, fn)

  def _saveImagesInRam(self):
    # Step 1: Save all images already in RAM.
    imgs = self._browser.body().selectAll('img')
    for img in imgs:
      src = img.tree()['src']
      if src.startswith('@'): continue
      src = self._browser.absolutifyUrl(src)
      if src not in self._srcs:
        ext = self._extension_from_url(src)
        self._srcs[src] = str(len(self._srcs)) + ext
        try:
          img.saveImageFromRAMAsPng(self._root + self._srcs[src])
        except Exception as e:    
          del self._srcs[src]
          print('Skipping \"%s\" due to error:' % src)
          print(e)
          continue
      img.js('self.setAttribute("src", "%s")' % ('@' + self._srcs[src]))

  def _downloadSrcsAndHrefs(self, dom):
    self._iterate(dom, lambda tag: self._handle_src_or_href(tag))
    self._iterate(dom, lambda tag: self._strip_at_char(tag))

  def _handle_src_or_href(self, tag):
    if tag.name == 'img':
      src = tag['src']
      if src.startswith('@'):
        return None
      src = self._browser.absolutifyUrl(src)
      ext = self._extension_from_url(src)
      if self.try_download(src, ext):
        tag['src'] = '@' + self._srcs[src]
    elif tag.name == 'link':
      attrs = tag.attrs
      if 'stylesheet' not in attrs['rel']:
        return None
      if 'type' in attrs and attrs['type'] != 'text/css':
        return None
      href = tag['href']
      if href.startswith('@'):
        return None
      href = self._browser.absolutifyUrl(href)
      if self.try_download(href, '.css'):
        tag['href'] = '@' + self._srcs[href]
    elif tag.name == 'script':
      attrs = tag.attrs
      if 'src' not in attrs:
        return None
      src = attrs['src']
      src = self._browser.absolutifyUrl(src)
      if self.try_download(src, '.js'):
        tag['src'] = '@' + self._srcs[src]

  def _strip_at_char(self, tag):
    if tag.name is None:
      return None
    attrs = tag.attrs
    if tag.name == 'img':
      if 'src' in attrs and tag['src'].startswith('@'):
        tag['src'] = tag['src'][1:]
    elif tag.name == 'link':
      if 'href' in attrs and tag['href'].startswith('@'):
        tag['href'] = tag['href'][1:]
    elif tag.name == 'script':
      if 'src' in attrs and tag['src'].startswith('@'):
        tag['src'] = tag['src'][1:]

  def recursively_download_stylesheets(self):
    did_download_new_stylesheet = True
    already_processed = set()
    while did_download_new_stylesheet:
      did_download_new_stylesheet = False
      for filename in os.listdir(self._root):
        if not filename.endswith('css'): continue
        if filename in already_processed: continue
        already_processed.add(filename)
        file_url = None
        for url in self._srcs:
          if self._srcs[url] == filename:
            file_url = url
            break
        if not file_url:
          sys.exit(1)
        with open(self._root + filename) as f:
          contents = f.read()
        urls_referenced = [match for match in re.finditer(r"""url\("[^"]+"\)|url\('[^']+'\)""", contents)]
        new_urls = []
        for url_referenced in urls_referenced:
          s = url_referenced.group()
          if '"' in s:
            url_to_ref = s[s.index('"')+1:s.rindex('"')]
          else:
            url_to_ref = s[s.index("'")+1:s.rindex("'")]
          url_to_ref = Browser.absolutifyUrlRelativetoPage(url_to_ref, file_url)
          if url_to_ref not in self._srcs:
            is_css = contents[:url_referenced.start()].endswith('@import ')
            if is_css:
              self.try_download(url_to_ref, '.css')
              did_download_new_stylesheet = True
            else:
              ext = self._extension_from_url(url_to_ref)
              self.try_download(url_to_ref, ext)
          new_urls.append(self._srcs[url_to_ref])
        for i in range(len(urls_referenced)-1, -1, -1):
          start, end = urls_referenced[i].span()
          new_import = 'url("%s")' % new_urls[i]
          contents = contents[:start] + new_import + contents[end:]
        with open(self._root + filename, 'w') as f:
          f.write(contents)

  # TODO: Make this smarter.
  def _extension_from_url(self, url):
    if '?' in url:
      url = url[:url.index('?')]
    return os.path.splitext(url)[1]

  # returns True iff this resource is downloaded by the end of this function call
  # (i.e. if the resource was already downloaded, it still returns True)
  def try_download(self, absolute_url, ext):
    if absolute_url in self._srcs:
      return True
    self._srcs[absolute_url] = str(len(self._srcs)) + ext
    try:
      self._browser.download(absolute_url, self._root + self._srcs[absolute_url])
      return True
    except:
      # Accept some failure.
      del self._srcs[absolute_url]
      return False





#########

# import seleniumwire.webdriver
# driver = seleniumwire.webdriver.Firefox()
# cs = CacheServer(driver, 'cache/')
# driver.get('http://xkcd.com/')
# cs.save()
#
# # Quit scraper.
# # Later...
#
# import seleniumwire.webdriver
# driver = seleniumwire.webdriver.Firefox()
# cs = CacheServer(driver, 'cache/')
# driver.get('http://xkcd.com/') # hit CacheServer for most requests
# cs.internet_enabled = False
# driver.get('http://xkcd.com/') # hit CacheServer or throw 404
# 
# # Note: due to browser limitations, you do still need to be connected
# # to the internet even if `internet_enabled` is `False`.
#
class CacheServer:
  def __init__(self, driver, root):
    assert root.endswith('/')
    self._root = root
    if os.path.exists(self._root):
      assert os.path.isdir(self._root)
    else:
      os.mkdir(root)
    if os.path.exists(self._root + 'index.json'):
      assert os.path.isfile(self._root + 'index.json')
      with open(self._root + 'index.json') as f:
        self._index = json.load(f)
    else:
      self._index = {}
    driver.request_interceptor = lambda request: self._request_interceptor(request)
    driver.response_interceptor = lambda request, response: self._response_interceptor(request, response)
    self.internet_enabled = True

  def _request_interceptor(self, request):
    print(request.url in self._index, self.internet_enabled, request.url)
    if request.url not in self._index:
      if not self.internet_enabled:
        request.create_response(status_code=404, headers=[], body=b'')
      return None
    resp = self._index[request.url]
    with open(self._root + resp['body'], 'rb') as f:
      body = f.read()
    request.create_response(status_code=resp['status_code'], headers=resp['headers'], body=body)

  def _response_interceptor(self, request, response):
    assert response == request.response
    if request.url in self._index: return None
    if not self.internet_enabled: return None
    data = seleniumwire.utils.decode(response.body, response.headers.get('Content-Encoding', 'identity'))
    with open(self._root + self._index[request.url]['body'], 'wb') as f:
      f.write(data)
    self._index[request.url] = {
      'status_code': response.status_code,
      'headers': response.headers.items(), # list<[str, str]>
      'body': str(len(self._index)),
    }

  def remove(self, url):
    del self._index[url]
    os.remove(self._index[url]['body'])

  def contains(self, url):
    return url in self._index

  def urls(self):
    return list(self._index.keys())

  def metadata(self, url):
    return json.loads(json.dumps(self._index[url]))

  def next_file_name(self):
    indices = set()
    for url in self._index:
      indices.add(int(self._index[url]['body']))
    for i in range(len(indices)):
      if i not in indices:
        return i
    return len(indices)

  def save(self):
    with open(self._root + 'index.json', 'w') as f:
      json.dump(self._index, f)





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





########## tests ##########

def assert_url_good(page_url, rel_path, exp):
  guess = Browser.absolutifyUrlRelativetoPage(rel_path, page_url)
  assert guess == exp, (page_url, rel_path, guess, exp)

assert_url_good('https://abc.xyz/foo/bar/index.html', 'img.jpg', 'https://abc.xyz/foo/bar/img.jpg')
assert_url_good('https://abc.xyz/foo/bar/', 'img.jpg', 'https://abc.xyz/foo/bar/img.jpg')
assert_url_good('https://abc.xyz/foo/bar/index.html', './img.jpg', 'https://abc.xyz/foo/bar/img.jpg')
assert_url_good('https://abc.xyz/foo/bar/', './img.jpg', 'https://abc.xyz/foo/bar/img.jpg')
assert_url_good('https://abc.xyz/foo/bar/index.html', '/img.jpg', 'https://abc.xyz/img.jpg')
assert_url_good('https://abc.xyz/foo/bar/', '/img.jpg', 'https://abc.xyz/img.jpg')
assert_url_good('https://abc.xyz/foo/bar/index.html', '../img.jpg', 'https://abc.xyz/foo/img.jpg')
assert_url_good('https://abc.xyz/foo/bar/', '../img.jpg', 'https://abc.xyz/foo/img.jpg')
assert_url_good('https://abc.xyz/foo/bar/index.html', '../../img.jpg', 'https://abc.xyz/img.jpg')
assert_url_good('https://abc.xyz/foo/bar/', '../../img.jpg', 'https://abc.xyz/img.jpg')
assert_url_good('https://www.girlspns.com/index.html', 'img.jpg', 'https://www.girlspns.com/img.jpg')
assert_url_good('https://www.girlspns.com/index.html', './img.jpg', 'https://www.girlspns.com/img.jpg')
assert_url_good('https://www.girlspns.com/index.html', '/img.jpg', 'https://www.girlspns.com/img.jpg')
