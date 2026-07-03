import os
from flask import Flask, jsonify, request, send_file

app = Flask(__name__)

# In-memory movies data
movies = [
    {
        "id": "1",
        "title": "Inception",
        "director": "Christopher Nolan",
        "year": 2010,
        "watched": True,
    },
    {
        "id": "2",
        "title": "Interstellar",
        "director": "Christopher Nolan",
        "year": 2014,
        "watched": False,
    },
    {
        "id": "3",
        "title": "Jurassic Park",
        "director": "Steven Spielberg",
        "year": 1993,
        "watched": True,
    },
]


def get_next_id():
    current_ids = [int(movie["id"]) for movie in movies if movie.get("id", "").isdigit()]
    return str(max(current_ids, default=0) + 1)


def find_movie(movie_id):
    return next((movie for movie in movies if movie["id"] == movie_id), None)


def parse_json_body():
    if not request.is_json:
        return None, jsonify({"error": "Request body must be valid JSON."}), 400
    payload = request.get_json(silent=True)
    if payload is None:
        return None, jsonify({"error": "Request body must be valid JSON."}), 400
    return payload, None, None


def parse_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value) if value is not None else default


def validate_movie_data(payload, require_all=True):
    errors = []
    title = (payload.get("title") or "").strip()
    director = (payload.get("director") or "").strip()
    year = payload.get("year")

    if require_all or "title" in payload:
        if not title:
            errors.append("title is required")
    if require_all or "director" in payload:
        if not director:
            errors.append("director is required")
    if require_all or "year" in payload:
        if year is None:
            errors.append("year is required")
        else:
            try:
                year = int(year)
                if year <= 0:
                    errors.append("year must be a positive integer")
            except (TypeError, ValueError):
                errors.append("year must be an integer")

    return errors


@app.route("/")
def index():
    return send_file(os.path.join(app.root_path, "index.html"))


# --- 1. READ ALL (With your Director filter) ---
@app.route("/movies", methods=["GET"])
def get_movies():
    director_q = (request.args.get("director") or "").strip()
    if director_q:
        filtered = [
            movie for movie in movies
            if movie.get("director", "").lower() == director_q.lower()
        ]
        return jsonify(filtered)
    return jsonify(movies)


@app.route("/movies", methods=["POST"])
def add_movie():
    payload, error_response, status = parse_json_body()
    if error_response is not None:
        return error_response, status

    errors = validate_movie_data(payload, require_all=True)
    if errors:
        return jsonify({"errors": errors}), 400

    new_movie = {
        "id": get_next_id(),
        "title": payload["title"].strip(),
        "director": payload["director"].strip(),
        "year": int(payload["year"]),
        "watched": parse_bool(payload.get("watched", False)),
    }
    movies.append(new_movie)
    return jsonify({"message": "Movie added successfully!", "movie": new_movie}), 201


@app.route("/movies/<movie_id>", methods=["GET"])
def get_movie(movie_id):
    movie = find_movie(movie_id)
    if movie is None:
        return jsonify({"error": "Movie not found."}), 404
    return jsonify(movie)


# --- 3. UPDATE (Toggle 'watched' status or change details) ---
@app.route("/movies/<movie_id>", methods=["PUT"])
def update_movie(movie_id):
    payload, error_response, status = parse_json_body()
    if error_response is not None:
        return error_response, status

    movie = find_movie(movie_id)
    if movie is None:
        return jsonify({"error": "Movie not found."}), 404

    errors = validate_movie_data(payload, require_all=False)
    if errors:
        return jsonify({"errors": errors}), 400

    if "title" in payload:
        movie["title"] = (payload.get("title") or movie["title"]).strip()
    if "director" in payload:
        movie["director"] = (payload.get("director") or movie["director"]).strip()
    if "year" in payload:
        movie["year"] = int(payload["year"])
    if "watched" in payload:
        movie["watched"] = parse_bool(payload["watched"], movie["watched"])

    return jsonify({"message": "Movie updated successfully!", "movie": movie})


# --- 4. DELETE (Remove a movie) ---
@app.route("/movies/<movie_id>", methods=["DELETE"])
def delete_movie(movie_id):
    movie = find_movie(movie_id)
    if movie is None:
        return jsonify({"error": "Movie not found."}), 404

    movies.remove(movie)
    return jsonify({"message": f"Movie with ID {movie_id} deleted successfully."})


if __name__ == "__main__":
    app.run(debug=True)
