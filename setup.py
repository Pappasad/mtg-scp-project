import os
import subprocess
import sys
import platform

venv_dir = '.venv'
install = ' install -r requirements.txt'

if not os.path.exists(venv_dir):
    print("Creating venv...")
    subprocess.check_call(['python', '-m', 'venv', venv_dir])
    print("Created venv.")
else:
    print("Venv exists.")

if os.path.exists(os.path.join(venv_dir, 'Lib', 'site-packages', 'pandas')):
    print("Requirements installed.")
else:
    print("Installing requirements...")
    if platform.system() == "Windows":   
        req_inst = os.path.join(venv_dir, 'Scripts', 'pip.exe') + install
    else:
        req_inst = os.path.join(venv_dir, 'bin', 'pip') + install
    subprocess.check_call(req_inst.split())
    print("Requirements installed.")


os.makedirs('cards', exist_ok=True)
os.makedirs('cc', exist_ok=True)

if os.path.exists('credentials.json'):
    print("Found credentials.")
else:
    foundjson = False
    for file in os.listdir(os.path.dirname(os.path.abspath(__file__))):
        if file.endswith('.json'):
            foundjson = True
            print(f"<<<CREDENTIAL ERROR>>> Couldn't find credentials but found {file}, if this is meant to be credentials, rename it to 'credentials.json'.")
            input("Press Any Key to Exit.")
            sys.exit()
    if not foundjson:
        print("<<<CREDENTIAL ERROR>>> No credential file detected. Please follow credential instructions")
        input("Press Any Key to Exit.")
        sys.exit()

input("Finished Setup! :) Press Any Key to Exit.")
