"""
Experiments with FindBy decorators
"""

from selenium.webdriver.common.by import By
from framework.browser import browser
from framework.components.element import UIElement
import settings


class FindBy():

    def __init__(self, value=None, by=By.XPATH):
        self.value = value
        self.by = by


    def __call__(self, f):
        @property
        def wrapper(*args, **kwargs):
            locator = (self.by, self.value)
            obj = f(*args, **kwargs)()
            obj.locator = locator
            return obj
        return wrapper


class LoginPage():

    @FindBy(By.XPATH, '//input[@id="__input1-inner"]')
    def username_txt(self): return UIElement

    @FindBy(By.XPATH, '//input[@id="__input2-inner"]')
    def password_txt(self): return UIElement

    @FindBy(By.XPATH, '//button[@id="__button2"]')
    def login_btn(self): return UIElement

    def open(self):
        browser.get(settings.URL)

    def login(self, username=settings.USERNAME, password=settings.PASSWORD):
        self.username_txt.send_keys(username)
        self.password_txt.send_keys(password)
        self.login_btn.click()

