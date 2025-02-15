import os
import json
import sqlite3
import requests
import subprocess
from flask import Flask, request, jsonify, send_file
from datetime import datetime
from PIL import Image
import pytesseract
import openai
import markdown

app = Flask(__name__)

# Security Constraints
DATA_DIR = "/data"
openai.api_key = os.getenv("AIPROXY_TOKEN")


def validate_path(path):
    """Ensures access is restricted to /data directory only."""
    if not path.startswith(DATA_DIR):
        return False
    return True


@app.route("/run", methods=["POST"])
def run_task():
    task = request.args.get("task", "").lower()
    
    try:
        if "install uv" in task and "datagen.py" in task:
            user_email = task.split()[-1]
            subprocess.run(["pip", "install", "uv"], check=True)
            subprocess.run(["python", "-m", "uv", "run", "datagen.py", user_email], check=True)
            return jsonify({"message": "Task A1 completed successfully."}), 200
        
        elif "format" in task and "prettier" in task:
            subprocess.run(["npx", "prettier@3.4.2", "--write", f"{DATA_DIR}/format.md"], check=True)
            return jsonify({"message": "Task A2 completed successfully."}), 200
        
        elif "count" in task and "wednesdays" in task:
            with open(f"{DATA_DIR}/dates.txt", "r") as f:
                dates = f.readlines()
            count = sum(1 for date in dates if datetime.strptime(date.strip(), "%Y-%m-%d").weekday() == 2)
            with open(f"{DATA_DIR}/dates-wednesdays.txt", "w") as f:
                f.write(str(count))
            return jsonify({"message": "Task A3 completed successfully."}), 200
        
        elif "sort" in task and "contacts" in task:
            with open(f"{DATA_DIR}/contacts.json", "r") as f:
                contacts = json.load(f)
            contacts.sort(key=lambda x: (x["last_name"], x["first_name"]))
            with open(f"{DATA_DIR}/contacts-sorted.json", "w") as f:
                json.dump(contacts, f, indent=4)
            return jsonify({"message": "Task A4 completed successfully."}), 200
        
        elif "email sender" in task:
            with open(f"{DATA_DIR}/email.txt", "r") as f:
                email_content = f.read()
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini", messages=[{"role": "system", "content": "Extract the sender's email address."},
                {"role": "user", "content": email_content}]
            )
            sender_email = response["choices"][0]["message"]["content"].strip()
            with open(f"{DATA_DIR}/email-sender.txt", "w") as f:
                f.write(sender_email)
            return jsonify({"message": "Task A7 completed successfully."}), 200
        
        elif "credit card" in task:
            img = Image.open(f"{DATA_DIR}/credit-card.png")
            card_number = pytesseract.image_to_string(img).replace(" ", "").strip()
            with open(f"{DATA_DIR}/credit-card.txt", "w") as f:
                f.write(card_number)
            return jsonify({"message": "Task A8 completed successfully."}), 200
        
        elif "sql query" in task:
            conn = sqlite3.connect(f"{DATA_DIR}/ticket-sales.db")
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(units * price) FROM tickets WHERE type = 'Gold'")
            result = cursor.fetchone()[0]
            conn.close()
            with open(f"{DATA_DIR}/ticket-sales-gold.txt", "w") as f:
                f.write(str(result))
            return jsonify({"message": "Task A10 completed successfully."}), 200
        
        else:
            return jsonify({"error": "Task not recognized."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/read", methods=["GET"])
def read_file():
    file_path = request.args.get("path")
    if not validate_path(file_path):
        return jsonify({"error": "Access denied."}), 403
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found."}), 404
    return send_file(file_path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
