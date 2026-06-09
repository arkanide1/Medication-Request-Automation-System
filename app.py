from gtts import gTTS
from flask import Flask, request, jsonify , send_file
import sqlite3
import re
import os
import json
from flask_cors import CORS
import requests
import tempfile
from keys import DEEPSEEK_API_KEY, API_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DB_PATH

app = Flask(__name__)
CORS(app)

print("Using DB path:", os.path.abspath(DB_PATH))


def connecter_a_la_base():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table';").fetchall()
            print("Tables dans la base de données :", tables)
    except Exception as e:
        print("Erreur de connexion à la base de données :", e)


@app.before_request
def log_request():
    print(f"\n=== Requête reçue ===")
    print(f"URL: {request.url}")
    print(f"Méthode: {request.method}")
    print(f"Headers: {dict(request.headers)}")
    print(f"Données: {request.get_json(silent=True)}\n")


def clean_medicament_name(name):
    return re.sub(r'\s+', ' ', name.strip().lower())


def chercher_medicament(nom_medicament, db_path=DB_PATH):
    try:
        print("Recherche pour:", nom_medicament)
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("""
                SELECT Libelle, Prix_m 
                FROM medicament 
                WHERE LOWER(Libelle) = LOWER(?)
            """, (nom_medicament,))
            rows = cursor.fetchall()

        print("Résultat brut:", rows)

        if rows:
            return {"status": "exists", "resultats": [{"libelle": lib, "prix": prix} for lib, prix in rows]}
        return {"status": "not_exists", "recherche": nom_medicament}

    except Exception as e:
        print("Erreur pendant la recherche:", e)
        return {"status": "erreur", "message": str(e)}


connecter_a_la_base()


@app.route('/chercher_medicament', methods=['POST'])
def api_chercher_medicament():
    try:
        data = request.get_json(force=True, silent=True)
        if not data or 'nom' not in data:
            return jsonify({"status": "error", "message": "Champ 'nom' requis"}), 400

        nom_medicament = clean_medicament_name(data['nom'])
        resultat = chercher_medicament(nom_medicament)

        return jsonify({
            "status": resultat["status"],
            "resultats": resultat.get("resultats", []),
            "recherche": nom_medicament
        })
    except Exception as e:
        print(f"Erreur globale: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


def fetch_med_info_deepseek(nom_medicament):
    api_url = API_URL
    api_key = DEEPSEEK_API_KEY

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = (
        f"Fournis uniquement une réponse au format JSON suivant, sans texte supplémentaire :\n\n"
        f"{{\n"
        f'  "nom": "{nom_medicament}",\n'
        f"  \"prix\": <prix en dollars>,\n"
        f"  \"description\": \"<courte description en français, max 50 mots>\"\n"
        f"}}\n\n"
        f"Le champ 'nom' doit être exactement '{nom_medicament}'."
    )

    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post(api_url, headers=headers, json=data)
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            print("Raw DeepSeek content:", content)  # Debug output

            # Extract JSON if it's wrapped in backticks
            if "```json" in content:
                match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
                if match:
                    content = match.group(1)

            try:
                return json.loads(content)
            except json.JSONDecodeError as decode_err:
                print("Échec du parsing JSON:", decode_err)
                return None
        else:
            print(f"Erreur DeepSeek: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"Erreur DeepSeek: {str(e)}")
        return None


@app.route('/search_web', methods=['POST'])
def recherche_web():
    print(f"Request received at /search_web")
    print(f"Request method: {request.method}")
    print(f"Request headers: {dict(request.headers)}")
    try:
        data = request.get_json(force=True, silent=True)
        print(f"Request data: {data}")
        if not data or 'recherche' not in data:
            return jsonify({"status": "error", "message": "Champ 'recherche' requis"}), 400

        nom_medicament = data['recherche']
        med_info = fetch_med_info_deepseek(nom_medicament)

        if med_info:
            return jsonify({"status": "ok", "data": med_info})

        return jsonify({"status": "no_result", "message": "Aucune information trouvée."}), 404

    except Exception as e:
        print(f"Erreur dans /search_web: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/text_to_speech', methods=['POST'])
def tts():
    data = request.json
    text = data.get('text', '')
    lang = data.get('lang', 'fr')

    tts = gTTS(text=text, lang=lang)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    tts.save(tmp.name)
    tmp.close()

    return send_file(tmp.name, mimetype='audio/mpeg')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10001)
