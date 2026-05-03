<!-- ABOUT THE PROJECT -->
## About The Project

If you want to learn about the variant of chess that this AI is made for, check out my repository for it [here](https://github.com/dylpykill/Infinity-Chess)

## The AI explained

https://github.com/dylanfaelker/Abbott-Chess-Engine/blob/main/Abbott_Explained.md

## Releases

https://github.com/dylanfaelker/Abbott-Chess-Engine/blob/main/Releases.md


<!-- GETTING STARTED -->
## Getting Started

It can be played on my website at [dylanfaelker.com](https://www.dylanfaelker.com/).

Go to Infinity Chess under projects, scroll down a little and click 'Play against chess AI (Abbott)'

### Project layout

* `app.py` is the Flask entrypoint
* `infinity_chess` houses the chess logic
* `engine` houses the engine logic
* `requirements.txt` defines Python dependencies
* `render.yaml` defines the Render web service

### Local development

1. Create and activate a virtual environment
2. Run `python -m venv .venv` to set up the venv
2. Run `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` to install the libraries
3. Run `.\.venv\Scripts\python.exe app.py` to run the server

The server will listen on `http://localhost:5000`.

On Windows, `requirements.txt` skips `gunicorn` automatically because Gunicorn is only used on Render's Linux runtime.

### Deploy on Render

1. Push this repository to GitHub
2. In Render, create a new Blueprint and point it at this repository
3. Render will read `render.yaml`
4. Render will install Python dependencies with `pip install -r requirements.txt`
5. Render will start the app with `gunicorn --bind 0.0.0.0:$PORT app:app`

If you prefer manual setup instead of a Blueprint, use these values in a Render Web Service:

* Runtime: `Python`
* Build Command: `pip install -r requirements.txt`
* Start Command: `gunicorn --bind 0.0.0.0:$PORT app:app`
* Health Check Path: `/health`



<!-- ROADMAP -->
## Roadmap

See the [open issues](https://github.com/othneildrew/Best-README-Template/issues) for a list of proposed features (and known issues).


## API endpoints
The API currently exposes:

* `GET /health`
* `POST /move`

`/move` returns the engines best move for a given position

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.



<!-- CONTACT -->
## Contact

Dylan Faelker - [linkedin](https://www.linkedin.com/in/dylanfaelker/)

Project Link: [https://github.com/dylpykill/Abbott-Chess-Engine](https://github.com/dylpykill/Abbott-Chess-Engine)

