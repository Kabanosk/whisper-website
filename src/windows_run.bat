@echo off

python "-m" "pip" "install" "-r" "..\requirements.txt"
git "clone" "git@github.com:openai\whisper.git"
python "run.py"
