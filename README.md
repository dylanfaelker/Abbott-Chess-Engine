<!-- ABOUT THE PROJECT -->
## About The Project

If you want to learn about the variant of chess that this AI is made for, check out my repository for it [here](https://github.com/dylpykill/Infinity-Chess)

### How the AI thinks

The AI creates a negamax tree of all the positions reachable after 1 full turn (1move black, 1 move white) and does a static evaluation from there. 
As it is going through the positions, it is also implementing a an alpha beta pruning algorithm to imporve efficiency,

In the static evaluation, the computer looks at three things.
 * How much material each team has (pieces).
 * How many squares each team controls. More points are given to control over points on the opposing side of the board to encourage attacking.
 * How safe the king is. How weak are the squares surrounding the king.

Chess piece are usually given this set of points.

Pawn = 1

Knight = 3

Bishop = 3

Rook = 5

Queen = 9

For infinity chess, I decided to give bishops 4 points because of how tricky they can be with the wrapping edge.

When calculating control of squares, squares are not counted multiple times. For example if a bishop and a kight are both attacking d4, the points are only given for control of d4 once.
If a team controls a square on its side of the board, 0.1 points are given.
If a team controls a square on the opponents side of the baord, 0.2 points are given.

King safety is mesured in the level of control of the squares the other team has around your teams king.
For each piece attacking a square near the king more than a piece defending that square, the level goes up. Note that the level cannot be negative. Also note that the kings defense of the square is not coutned. For example, if the king is on h2 and there is a bishop and knight attacking that h3 with only a queen defending it, the level is 1. However, if two pawns are supporting it then the level is 0.
0.25 points are taken for each level of weakness around your king.




<!-- GETTING STARTED -->
## Getting Started

It can be played on my website at [dylanfaelker.com](https://www.dylanfaelker.com/).

Go to Infinity Chess in the menu bar, scroll down a little and click 'Play against chess AI (Abbott)'

### Project layout

* `app.py` is the Flask entrypoint
* `infinity_chess` houses the chess logic
* `engine` houses the engine logic
* `requirements.txt` defines Python dependencies
* `render.yaml` defines the Render web service

### Local development

1. Create and activate a virtual environment
2. Run `pip install -r requirements.txt`
3. Run `python app.py`

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

