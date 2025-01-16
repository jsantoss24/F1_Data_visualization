from app import app  # Importa la instancia de la aplicación Dash

# Dash usa Flask internamente, así que exponemos su servidor subyacente
server = app.server

if __name__ == "__main__":
    app.run_server(debug=True)
