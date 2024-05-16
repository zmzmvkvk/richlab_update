from selenium import webdriver

driver = webdriver.Chrome()
driver.get("https://www.example.com")
print(driver.title)
driver.quit()
