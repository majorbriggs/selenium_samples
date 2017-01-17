from selenium.webdriver.common.by import By
from framework.browser import browser, wait_until_dom_is_loaded, wait_until_there_are_no_loaders
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import time
import autodoc.api
import logconf


logger = logconf.get_logger(__name__)


class UIElement():

    _parents_stack = []
    _toplevel = False
    _locator = None

    @property
    def visible(self):
        try:
            if self.locate(timeout=0.5).is_displayed() == True:
                return True
            return False
        except:
            return False

    def __init__(self, toplevel=False):
        _toplevel = self._toplevel or toplevel
        if UIElement._parents_stack and not _toplevel:
            self.parent_ui_element = UIElement._parents_stack[-1]
        else:
            self.parent_ui_element = None
        self.locator = None or self._locator
        self.i = None

    def _set_index(self, i):
        self.i = i
        return self

    @property
    def element(self):
        return self.locate()

    @autodoc.api.take_screenshot
    def locate(self):
        if not self.locator:
            raise NotImplementedError

        if self.parent_ui_element:
            parent = self.parent_ui_element.locate()

            try:
                if self.i:
                    element = parent.find_elements(*self.locator)[self.i]
                else:
                    element = parent.find_element(*self.locator)

            except WebDriverException as e:
                msg = e.msg
                if isinstance(e, NoSuchElementException):
                    msg += '\n\nEnsure that {}\n\nis a valid parent for the element'.format(self.parent_ui_element)
                raise WebDriverException(msg=msg)

        else:
            if self.i:
                element = browser.find_elements(*self.locator)[self.i]
            else:
                element = browser.find_element(*self.locator)

        return element

    def locate_multiple(self):
        if not self.locator:
            raise NotImplementedError
        elif self.parent_ui_element:
            elements = self.parent_ui_element.locate().find_elements(*self.locator)
            ui_list = [self.__class__().located_by(self.locator).with_parent(self.parent_ui_element)._set_index(i) for i, e in enumerate(elements)]
        else:
            elements = browser.find_elements(*self.locator)
            ui_list = [self.__class__().located_by(self.locator)._set_index(i) for i, e in enumerate(elements)]
        return UIElementsList(ui_list)

    def located_by(self, locator):
        self.locator = locator
        return self

    def located_by_xpaths(self, xpaths_list):
        xpaths = "|".join("({})".format(xpath) for xpath in xpaths_list)
        return self.located_by((By.XPATH, xpaths))

    def located_by_xpath(self, xpath):
        return self.located_by((By.XPATH, xpath))

    def located_by_css_selector(self, css_selector):
        return self.located_by((By.CSS_SELECTOR, css_selector))

    def located_by_id(self, id):
        return self.located_by((By.ID, id))

    def located_by_link_text(self, link_text):
        return self.located_by((By.LINK_TEXT, link_text))

    def located_by_partial_link_text(self, partial_link_text):
        return self.located_by((By.PARTIAL_LINK_TEXT, partial_link_text))

    def with_parent(self, parent_ui_element):
        self.parent_ui_element = parent_ui_element
        return self

    def subelement(self, _class=None):
        if _class is None:
            _class = UIElement
        obj = _class()
        obj.parent_ui_element = self
        return obj

    def highlight(self):
        browser.execute_script("arguments[0].setAttribute('style', arguments[1]);", self.element,
                              "border: 3px solid red;")
        time.sleep(0.5)
        browser.execute_script("arguments[0].setAttribute('style', arguments[1]);", self.element, "")

    def as_list(self):
        return gui_interaction(
            lambda: self.locate_multiple(),
            'Getting list of {}'.format(self)
        )

    def hover(self):
        return gui_interaction(
            lambda: ActionChains(browser).move_to_element(self.locate()).perform(),
            'Hover on {}'.format(self)
        )

    def native_click(self):
        return gui_interaction(
            lambda: ActionChains(browser).move_to_element(self.locate()).click().perform(),
            'Native click on {}'.format(self)
        )

    def click(self):
        gui_interaction(
            lambda: self.locate().click(),
            'Click on {}'.format(self)
        )

    def send_keys(self, *keys_to_send):
        gui_interaction(
            lambda: self.locate().send_keys(*keys_to_send),
            'Sending keys "{}" to {}'.format(keys_to_send, self)
        )

    def get_attribute(self, attr):
        return gui_interaction(
            lambda: self.locate().get_attribute(attr),
            'Getting attribute "{}" from {}'.format(attr, self)
        )

    def text(self):
        return gui_interaction(
            lambda: self.locate().text,
            'Getting text from {}'.format(self)
        )

    def __enter__(self):
        UIElement._parents_stack.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        UIElement._parents_stack.pop()

    def __str__(self):
        return '{} located by {}'.format(self.__class__, self.locator)


class UIElementsList(list):

    def highlight(self):
        for e in self:
            e.highlight()


def gui_interaction(action, message):
    wait_until_dom_is_loaded()
    wait_until_there_are_no_loaders()

    n = 3
    while n:
        n -= 1
        try:
            return action()
        except WebDriverException as e:
            logger.warn('{} failed\n{}'.format(message, e.msg))
            if n == 0:
                raise e
        time.sleep(1)
