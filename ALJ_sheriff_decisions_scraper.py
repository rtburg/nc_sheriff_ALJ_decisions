from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

# Initialize the Firefox WebDriver with download preferences
options = webdriver.FirefoxOptions()
options.set_preference("browser.download.folderList", 2)  # Use custom download directory
options.set_preference("browser.download.dir", "~/Documents/Sheriff Education Training Standards Division/ALJ_decisions")
options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
options.set_preference("pdfjs.disabled", True)  # Disable the built-in PDF viewer, so the PDF is downloaded automatically

driver = webdriver.Firefox(options=options)

# Load the form page
url = "https://www.encoah.oah.state.nc.us/publicsite/search"
driver.get(url)

# Add a delay to allow the page to fully load
time.sleep(2)

# Select the Case Type dropdown and submit the form
try:
    case_type_dropdown = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//select[contains(@name, 'ddlCaseType')]"))
    )
    select = case_type_dropdown
    select.send_keys('Sheriffs Education & Training Standards')  # Selecting by visible text
except Exception as e:
    print("Error finding Case Type dropdown: ", e)

# Try to find and submit the form by clicking the button
try:
    submit_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' or @value='Search']"))
    )
    submit_button.click()
except Exception as e:
    print("Error finding or clicking submit button: ", e)

# Function to wait for the PDF to finish downloading
def wait_for_download(download_dir, timeout=120):
    """ Wait for the download to finish by checking for the absence of .part files """
    seconds = 0
    while seconds < timeout:
        time.sleep(1)
        files = os.listdir(download_dir)
        if not any(file.endswith('.part') for file in files):  # No incomplete downloads
            return True
        seconds += 1
    return False  # Timed out waiting for download to complete

# Function to retry the click action for the "View" image
def retry_click_view_image(view_img_xpath, retries=3):
    for attempt in range(retries):
        try:
            view_img = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, view_img_xpath))
            )
            print(f"Attempt {attempt + 1}: Found 'View' image, clicking now...")
            view_img.click()
            return True  # Success
        except Exception as e:
            print(f"Attempt {attempt + 1}: Failed to click 'View' image: {e}")
            time.sleep(2)  # Retry after short delay
    return False  # Failed after retries

# Wait for the results table to load after form submission
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'tblResults'))
    )
    print("Results loaded, proceeding to click on each link.")
    
    # Track how many links have been processed
    total_links = len(driver.find_elements(By.XPATH, "//table[@id='tblResults']//a"))
    
    for index in range(total_links):
        try:
            # Re-fetch the list of <a> tags after returning to the results page
            pdf_links = driver.find_elements(By.XPATH, "//table[@id='tblResults']//a")
            
            # Click the current link
            print(f"Clicking on link {index + 1}")
            pdf_links[index].click()

            # Add a delay to allow the page to load
            time.sleep(3)

            # Now, look for the link with text "Docket" on the new page and click it
            try:
                docket_link = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.LINK_TEXT, "Docket"))
                )
                print(f"Clicking on 'Docket' link for link {index + 1}")
                docket_link.click()

                # Add a delay to allow the Docket page to load
                time.sleep(3)

                # Now find the <span id="lblStyle"> and extract text before the first <br>
                try:
                    lbl_style_span = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "lblStyle"))
                    )
                    lbl_style_text = lbl_style_span.get_attribute("innerHTML").split("<br>")[0].strip()
                    print(f"Unique filename extracted: {lbl_style_text}")

                    # Now find the <img> tag with title "View" and click it to open the PDF in a new tab
                    try:
                        if retry_click_view_image("//img[@title='View']"):
                            print(f"Successfully clicked 'View' image for link {index + 1}")
                            
                            # Wait for the PDF to download
                            download_dir = "~/Documents/Sheriff Education Training Standards Division/ALJ_decisions"
                            if wait_for_download(download_dir):
                                # Rename the PDF file with the extracted name
                                downloaded_file = max([f for f in os.listdir(download_dir)], key=lambda f: os.path.getctime(os.path.join(download_dir, f)))
                                new_file_name = f"{lbl_style_text}.pdf"
                                os.rename(os.path.join(download_dir, downloaded_file), os.path.join(download_dir, new_file_name))
                                print(f"PDF saved as: {new_file_name}")
                            else:
                                print(f"Warning: Timeout waiting for the PDF to download for link {index + 1}")

                        else:
                            print(f"Error: Could not click 'View' image after multiple attempts for link {index + 1}")

                    except Exception as e:
                        print(f"Warning: Error finding 'View' image or downloading PDF for link {index + 1}: {e}")

                    # Now click on the "Return to Search Results" link to go back
                    try:
                        return_link = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//a[contains(@onclick, '__doPostBack') and contains(text(), 'Return to Search Results')]"))
                        )
                        print(f"Clicking 'Return to Search Results' link for link {index + 1}")
                        return_link.click()

                        # After returning to the results page, wait for it to load again
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, 'tblResults'))
                        )
                        print(f"Returned to results for next link.")

                    except Exception as e:
                        print(f"Error clicking 'Return to Search Results' for link {index + 1}: {e}")

                except Exception as e:
                    print(f"Error extracting text from lblStyle for link {index + 1}: {e}")

            except Exception as e:
                print(f"Error finding or clicking 'Docket' link for link {index + 1}: {e}")

        except Exception as e:
            print(f"Error clicking or navigating back for link {index + 1}: {e}")

except Exception as e:
    print("Error waiting for or clicking links: ", e)

# Close the browser after scraping
driver.quit()
