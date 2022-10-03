@echo off

pip "install" "-r" "..\requirements.txt"
git "clone" "git@github.com:openai\whisper.git"
python3 "run.py"
