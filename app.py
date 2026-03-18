from flask import Flask, jsonify
from flask_cors import CORS
from services.trading import generate_signal

app = Flask(__name__)
CORS(app)

@app.route("/signal", methods=["GET"])
def signal():
    signal, score = generate_signal()

    if signal is None:
        return jsonify({"error": "Failed to fetch data"}), 500

    return jsonify({
        "pair": "EUR/USD",
        "signal": signal,
        "score": score
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))