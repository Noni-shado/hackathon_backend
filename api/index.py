import sys
import os

# IMPORTANT pour que "app/" soit importable sur Vercel
sys.path.append(os.getcwd())

from app.main import app
