# wsgi.py
import os  # Asegúrate de importar os
from app import app  # Importa la instancia de la app

if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 8050)))
