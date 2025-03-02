from flask import Flask, jsonify, request
from rapidfuzz import fuzz, process

app = Flask(__name__)

@app.route("/search", methods=['POST'])
def search():
    data = request.json  # Get JSON data from the request body
    jsonify({"message": "Data received", "data": data}), 200
    results = process.extract(["hi there"], ["there hi", "hi there", "hi, there!"], scorer=fuzz.token_sort_ratio)
    string = ""
    for result in results:
        string += str(result) + " "
    return string # [100. 100. 88.888885] not sure why it isn’t a concatenated string