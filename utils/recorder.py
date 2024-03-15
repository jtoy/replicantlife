import os
import sys
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from obswebsocket import obsws, requests


load_dotenv()

# OBS Studio Websocket Settings
obs_settings = {
    "obs_host": os.environ.get("OBS_HOST","127.0.0.1"),
    "obs_port": int(os.environ.get("OBS_PORT",4455)),
    "obs_password": os.environ.get("OBS_PASSWORD"),
    "record_path": os.environ.get("RECORD_PATH","movies"),
}

# This is NOT working yet
# Start recording based on a javacript event.
def start_recording_if_playing():
    is_playing = driver.execute_script("return isPlaying;")
    if is_playing:
        start_recording = requests.StartRecord()
        ws.call(start_recording)
        print("Recording started")

# Set up Chrome options to start in full-screen mode
chrome_options = Options()
chrome_options.add_argument('--kiosk')
chrome_options.add_experimental_option("excludeSwitches", ['enable-automation']);


# Create a WebDriver instance (make sure you have the ChromeDriver executable in your PATH)
driver = webdriver.Chrome(options=chrome_options)

url_path = sys.argv[1] if len(sys.argv) > 1 else "https://replicantlife.com/"
driver.get(url_path) # Open a website

# Allow some time for the page to load
time.sleep(3)

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

# Start recording in OBS Studio
start_recording = requests.StartRecord()
ws.call(start_recording)

# The function is NOT working yet.
# start_recording_if_playing()

# Continue recording for 20s (adjust as needed)
time.sleep(20)

# Stop recording in OBS Studio
stop_recording = requests.StopRecord()
ws.call(stop_recording)

# Close the browser when done
driver.quit()

# Disconnect from OBS Studio
ws.disconnect()
