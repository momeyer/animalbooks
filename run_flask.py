#!/usr/bin/python3.6

import os
import subprocess

os.environ["FLASK_APP"] = "application.py"
os.environ["FLASK_DEBUG"] = "1"

subprocess.call(['flask', 'run'])
