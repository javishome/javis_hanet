import os
# define an extension that will be cythonized and compiled
#convert to .so file
current_dir = os.getcwd()
# copy __init__.py to encode folder
for file in os.listdir("__pycache__"):
    if file.startswith("__init__") and file.endswith(".pyc"):
        file_parts = file.split(".")
        os.rename("__pycache__/" + file,file_parts[0] + ".pyc")

# remove __init__.py from  folder
if os.path.exists("__init__.py"):
    os.remove("__init__.py")


