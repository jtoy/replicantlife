import os
import sys
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from obswebsocket import obsws, requests

load_dotenv()

# OBS Studio Websocket Settings
obs_settings = {
    "obs_host": os.environ.get("OBS_HOST","127.0.0.1"),
    "obs_port": int(os.environ.get("OBS_PORT",4455)),
    "obs_password": os.environ.get("OBS_PASSWORD"),
    "record_path": os.environ.get("RECORD_PATH","movies"),
}

# Set up Chrome options to start in full-screen mode
chrome_options = Options()
chrome_options.add_argument('--kiosk')
chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])

# Create a WebDriver instance (make sure you have the ChromeDriver executable in your PATH)
driver = webdriver.Chrome(options=chrome_options)

url_path = sys.argv[1] if len(sys.argv) > 1 else "https://replicantlife.com/"
driver.get(url_path) # Open a website

# Allow some time for the page to load
time.sleep(2)

# Pretend to interact with the app to enable audio autoplay
actions = ActionChains(driver)
actions.move_by_offset(100, 100)
actions.click().perform()

# Connect to OBS Studio via WebSocket
ws = obsws(obs_settings["obs_host"], obs_settings["obs_port"], obs_settings["obs_password"])
ws.connect()

# Set the recording path in OBS Studio
recording_path = obs_settings["record_path"]
set_recording_path = requests.SetRecordDirectory(recording_path=recording_path)
ws.call(set_recording_path)

# Check current recording status
current_recording_status = ws.call(requests.GetRecordStatus())
print("Current recording status:", current_recording_status)

try:
    # Wait for simulation to start
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "simulationStarted"))
    )

    # Start recording in OBS Studio
    start_recording = requests.StartRecord()
    ws.call(start_recording)
    print("Recording started")

    # Wait for simulation to complete
    WebDriverWait(driver, 600).until(
        EC.presence_of_element_located((By.ID, "simulationComplete"))
    )

finally:
    # Stop recording in OBS Studio
    stop_recording = requests.StopRecord()
    ws.call(stop_recording)
    print("Recording stopped")

    # Close the browser when done
    driver.quit()

    # Disconnect from OBS Studio
    ws.disconnect()
