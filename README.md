## Website which convert speech to text by Whisper model ([Official Repo](https://github.com/openai/whisper))

## Hosting website on localhost:

1. Clone the repo - `git clone git@github.com:Kabanosk/website_for_whisper.git`

### Host using uvicorn
1. install uvicorn with command like `apt install uvicorn` / `pacman -S uvicorn`
2. go to src directory - `cd website_for_whisper/src`
3. host website on localhost - `uvicorn main:app --reload`
