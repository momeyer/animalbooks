import os
import pathlib
import unittest

from selenium import webdriver

# A convenience function to turn a filename into a full path, as needed for a browser
def file_uri(filename):
    return pathlib.Path(os.path.abspath(filename)).as_uri()

driver = webdriver.Chrome()

class WebpageTests(unittest.TestCase):

    def test_login(self):
        driver.get(file_uri("index.html"))
        self.assertEqual(driver.title, "Animal Books")

    
if __name__ == "__main__":
    unittest.main()