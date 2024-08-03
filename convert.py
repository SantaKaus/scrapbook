import os

path = 'static/images'
print("Directory exists:", os.path.exists(path))
print("Directory writable:", os.access(path, os.W_OK))
