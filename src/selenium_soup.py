
import base64
import bs4
import json
import os
import pyautogui # pip3 install pyautogui
import re
import selenium.webdriver.support.expected_conditions
import selenium.webdriver.support.ui
import selenium.webdriver.common.by
import seleniumwire.webdriver
import seleniumwire.utils
import sqlite3
import time
import urllib.request
import urllib.parse
import threading

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
      # TODO: Consider `== bs4.element.Tag` instead.
      tmp = list(filter(lambda x: type(x) != bs4.element.NavigableString, self._tree.children))
      if len(tmp) == 2:
        # This is very rare and poorly understood.
        # https://asstr.xyz/files/Authors/TheMysteriousMrLeeOrganization/
        self._tree = tmp[0]
      else:
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
      self.setAttribute('crossOrigin', 'anonymous');
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

  # TODO: Test this.
  def waitForImageToLoad(timeout=0):
    self.js("""
      if (self.complete) {
        return Promise.resolve();
      }
      return new Promise((resolve) => {
        setTimeout(_ => {
          resolve();
        }, %i);
        image.addEventListener('onload', _ => {
          resolve();
        })
      });
      return;
    """ % timeout)

  # Consider saving the image as a png, jpeg, or webp. Actually save whichever is smallest.
  # TODO: Test.
  def saveImageFromRAM(self, path):
    assert self._tree.name == 'img'
    # https://stackoverflow.com/a/61061867
    script = """
      {
        let info = {};

        let blobFromImage = (img, type) => {
          let canvas = document.createElement('canvas');
          let context = canvas.getContext('2d');
          canvas.height = img.naturalHeight;
          canvas.width = img.naturalWidth;
          context.drawImage(img, 0, 0, img.naturalWidth, img.naturalHeight);
          return new Promise((resolve, reject) => {
            canvas.toBlob(blob => {resolve(blob);}, 'image/' + type)
          });
        };

        let base64FromArrayBuffer = (arrayBuffer) => {
          let binary = '';
          const bytes = new Uint8Array(arrayBuffer);
          const len = bytes.byteLength;
          for (let i = 0; i < len; i++) {
            binary += String.fromCharCode(bytes[i]);
          }
          return window.btoa(binary);
        };

        let promises = [];
        let types = ['png', 'jpeg', 'webp'];
        self.setAttribute('crossOrigin', 'anonymous');
        info['times'] = [];
        info['times'].push(['start', new Date().getTime()]);
        if (!self.complete) {
          info['error'] = 'image was not finished loading';
          return [null, null, info];
        }
        for (let type in types) {
          promises.push(blobFromImage(self, type));
        }
        return Promise.all(promises).then(blobs => {
          info['times'].push(['blobed', new Date().getTime() - info['times'][0][1]]);
          let minSize = 1e200;
          let minIndex = -1;
          for (let i = 0; i < blobs.length; ++i) {
            if (blobs[i] != null && blobs[i].size < minSize) {
              minSize = blobs[i].size;
              minIndex = i;
            }
          }
          if (minIndex == -1) {
            if (!('error' in info)) {
              info['error'] = 'failed to generate any blobs';
            }
            return null;
          }
          return [types[minIndex], blobs[minIndex]]
        }).then(type_blob => {
          if (type_blob == null) {
            return null;
          }
          info['times'].push(['selected', new Date().getTime() - info['times'][0][1]]);
          return new Promise((resolve, reject) => {
            let reader = new FileReader();
            reader.addEventListener("loadend", function() {
               info['times'].push(['arrayed', new Date().getTime() - info['times'][0][1]]);
               resolve([type_blob[0], reader.result])
            });
            reader.readAsArrayBuffer(type_blob[1]);
          });
        }).then(type_arrayBuffer => {
          if (type_arrayBuffer == null) {
            if (!('error' in info)) {
              info['error'] = 'failed to convert blob to ArrayBuffer';
            }
            return [null, null, info];
          }
          let base64String = base64FromArrayBuffer(type_arrayBuffer[1]);
          info['times'].push(['stringed', new Date().getTime() - info['times'][0][1]]);
          return [type_arrayBuffer[0], base64String, info];
        });
      }
      """
    # Example time allocation:
    #   13 ms - [info] converting the image into a Blob
    #    0 ms - [info] selecting a Blob
    #    0 ms - [info] converting Blob to ArrayBuffer
    #    8 ms - [info] converting ArrayBuffer to base64 string
    #    7 ms - getting the data to and from the browser
    results = self.js(script)
    if not results:
      return None, 'Unknown error'
    assert len(results) == 3, results
    extension, base64String, info = results
    if extension is None:
      assert base64String is None
      assert 'error' in info
      return None, info['error']
    #    0 ms - converting from `base64String` to `data`.
    data = base64.b64decode(base64String)
    #    0 ms - writing to file
    with open(path + '.' + extension, "wb") as f:
      f.write(data)
    return extension, None






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

  def navigateTo(self, url, timeOut=10, extraTime=0.5):
    self._reddingIDCounter = 0
    self._body = None
    self._browser.get(url)
    self.waitForPageToLoad(timeOut, extraTime=0.5)

  def waitForPageToLoad(self, timeOut, extraTime=0.5):
    self.withFor(timeOut, lambda browser: browser.js('return document.readyState;') == 'complete')
    time.sleep(extraTime)

  def withFor(self, timeOut, fn):
    # Wait for the page to load.
    time.sleep(0.1)
    startTime = time.time()
    while True:
      if time.time() - startTime > timeOut:
        assert False, "Took more than %i seconds to load the page" % timeOut
      time.sleep(0.1)
      if fn(self): break

  def waitForSelector(self, cssSelector, timeOut=10):
    return selenium.webdriver.support.ui.WebDriverWait(self._browser, timeOut).until(selenium.webdriver.support.expected_conditions.presence_of_element_located((selenium.webdriver.common.by.By.CSS_SELECTOR, cssSelector)))

  def body(self, noCache=False):
    # If the body is cached and hasn't been replaced by a page-navigations, just return it.
    if noCache:
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

  def js(self, javascript):
    return self._browser.execute_script(javascript)

  def download(self, url, path):
    userAgent = self._browser.execute_script("return navigator.userAgent;")
    url = self.absolutifyUrl(url)
    cookies = self._browser.get_cookies()
    Browser.download_basic(url, path, userAgent, cookies)

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
  def download_basic(cls, url, path, userAgent=None, cookies=None):
    headers = []
    if userAgent:
      headers.append(('User-Agent', userAgent))
    if cookies:
      cookiesStr = ''
      for cookie in cookies:
        # TODO: This probably needs to be improved.
        cookieStr = cookie['name'] + '=' + cookie['value'] + ';'
        cookiesStr += cookieStr
      headers.append(('Cookie', cookiesStr))
    opener = urllib.request.build_opener()
    opener.addheaders = headers
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
  def persistentChromeDriver(cls, driverPath, userDataPath, profileDirectory):
    options = selenium.webdriver.chrome.options.Options()
    options.add_argument("user-data-dir=%s" % userDataPath)
    options.add_argument('profile-directory=%s' % profileDirectory)
    return selenium.webdriver.Chrome(executable_path=driverPath, chrome_options=options)

  # TODO: Test
  @classmethod
  def persistentWireChromeDriver(cls, driverPath, userDataPath, profileDirectory):
    options = selenium.webdriver.chrome.options.Options()
    options.add_argument("user-data-dir=%s" % userDataPath)
    options.add_argument('profile-directory=%s' % profileDirectory)
    return seleniumwire.webdriver.Chrome(executable_path=driverPath, chrome_options=options)

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
  def save_page_system(self, path_relative_to_save_dialog):
    pyautogui.hotkey('command', 's')
    # First time will likely prompt user for OS permission.
    time.sleep(1)
    pyautogui.typewrite(path_relative_to_save_dialog)
    pyautogui.hotkey('enter')

  def save_page_recursive(self, path):
    pd = PageRecursiveDownloader(self, path)





########## PageRecursiveDownloader ##########

# Recursively download a webpage and all its resources.
class PageRecursiveDownloader:
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
# cs.internet_mode = 0
# driver.get('http://xkcd.com/') # hit CacheServer or throw 404
# 
# # Note: due to browser limitations, you do still need to be connected
# # to the internet even if `internet_mode` is `0`.
#
class CacheServer:
  def __init__(self, driver, dbpath):
    assert type(dbpath) == str
    # https://stackoverflow.com/questions/64150072/sqlite3-programmingerror-sqlite-objects-created-in-a-thread-can-only-be-used-in
    # All public methods outside the initializer must be wrap their contents with `with self._mutex:`,
    # as must the two "interceptor" methods when doing SQL operations.
    self._mutex = threading.Lock()
    self._db = sqlite3.connect(dbpath, check_same_thread=False)
    self._cursor = self._db.cursor()
    self._cursor.execute("""
      CREATE TABLE IF NOT EXISTS cache(
        url TEXT,
        status_code INTEGER,
        headers TEXT,
        unix_time INTEGER,
        body BLOB
      );
    """)
    self._cursor.execute("""
      CREATE INDEX IF NOT EXISTS url_index ON cache(url, unix_time);
    """)
    driver.request_interceptor = lambda request: self._request_interceptor(request)
    driver.response_interceptor = lambda request, response: self._response_interceptor(request, response)
    # Whether the browser is allowed to hit the internet.
    # Note: if this is `False`, then a natural consequence is nothing will be added to the cache.
    self.internet_enabled = True

    # 0 - don't write internet-responses to the cache
    # 1 - add novel URLs' responses to the cache
    # 2 - add novel URLs' responses to the cache; overwrite existing URLs' responses in the cache
    # 3 - add novel URLs' responses to the cache; add existing URLs' responses to the cache
    self.cache_write_mode = 1

    # Number of seconds back in time to check the cache.
    # Note 1: Entries in the cache are never automatically cleared; merely ignored.
    # Note 2: If `ttl = 0`, then the cache is never read.
    # Note 3: If `ttl = inf`, then every item in the cache is fair game.
    self.ttl = 99999999999
    # Number of requests that got through the cache.
    # Useful to track real QPS.
    self.requestCount = 0
    self.disable_cors_security = False

  def remove(self, url):
    assert type(url) == str
    with self._mutex:
      self._cursor.execute("""
        DELETE FROM cache WHERE url = ?;
      """, (url,))

  def contains(self, url):
    assert type(url) == str
    with self._mutex:
      return self._contains(url)

  def commit(self):
    with self._mutex:
      self._db.commit()

  def close(self):
    with self._mutex:
      self._db.close()

  def all(self):
    with self._mutex:
      result = self._cursor.execute("""
        SELECT url, status_code, unix_time FROM cache
      """)
    rows = result.fetchall()
    rtn = []
    for row in rows:
      rtn.append({
        'url': row[0],
        'status_code': row[1],
        'unix_time': row[2],
      })
    return rtn

  def get(self, url):
    with self._mutex:
      return self._getFromCache(url)

  def _contains(self, url):
    result = self._cursor.execute("""
      SELECT 1 FROM cache WHERE url = ? AND unix_time >= ? LIMIT 1;
    """, (url, int(time.time() - self.ttl)))
    return result.fetchone() is not None

  def _request_interceptor(self, request):
    with self._mutex:
      result = self._getFromCache(request.url)
    if result:
      request.create_response(status_code=result['status_code'], headers=result['headers'], body=result['body'])
    elif self.internet_enabled:
      self.requestCount += 1
      pass # let browser do its thing
    else:
      request.create_response(status_code=404, headers=[], body=b'')

  def _response_interceptor(self, request, response):
    assert response == request.response
    if self.disable_cors_security:
      response.headers['Access-Control-Allow-Origin'] = '*'
    if not self.internet_enabled:
      return None
    if self.cache_write_mode == 0:
      return None
    body = self._bodyFromResponse(response)
    with self._mutex:
      if self.cache_write_mode == 1:
        if not self._contains(request.url):
          self._addToCache(request.url, response, body)
      elif self.cache_write_mode == 2:
        if self._contains(request.url):
          self._updateCacheItem(request.url, response, body)
        else:
          self._addToCache(request.url, response, body)
      elif self.cache_write_mode == 3:
        self._addToCache(request.url, response, body)
      else:
        assert False, self.cache_write_mode

  def _addToCache(self, url, response, body):
    assert type(url) == str
    self._cursor.execute("""
      INSERT INTO cache(url, status_code, headers, unix_time, body)
      VALUES (?, ?, ?, ?, ?);
    """, (url, response.status_code, json.dumps(response.headers.items()), int(time.time()), body))

  def _updateCacheItem(self, url, response, body):
    assert type(url) == str
    self._cursor.execute("""
      UPDATE cache
      SET status_code=?, headers=?, unix_time=?, body=?
      WHERE url=?;
    """, (response.status_code, json.dumps(response.headers.items()), int(time.time()), body, url))

  def _bodyFromResponse(self, response):
    return seleniumwire.utils.decode(response.body, response.headers.get('Content-Encoding', 'identity'))

  def _getFromCache(self, url):
    result = self._cursor.execute("""
      SELECT url, status_code, headers, unix_time, body
      FROM cache
      WHERE url = ?  AND unix_time >= ?
      ORDER BY unix_time DESC
      LIMIT 1;
    """, (url, int(time.time() - self.ttl)))
    data = result.fetchone()
    if data is None:
      return None
    return {
      'url': data[0],
      'status_code': data[1],
      'headers': json.loads(data[2]),
      'unix_time': data[3],
      'body': data[4],
    }





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
