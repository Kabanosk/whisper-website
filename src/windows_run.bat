@echo off

python3 "-m" "pip" "install" "-r" "%CD%.\requirements.txt"
git "clone" "git@github.com:openai\whisper.git"
python3 "run.py"
