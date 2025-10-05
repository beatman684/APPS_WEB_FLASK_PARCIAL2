from flask import Flask, render_template

# Aplicación Flask
def create_app():
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template("index.html", title="Inicio")

    @app.get("/about")
    def about():
        return render_template("about.html", title="Acerca de")

    # Manejador básico de 404
    @app.errorhandler(404)
    def not_found(e):
        return render_template("index.html", title="No encontrado"), 404

    return app

# Objeto de aplicación para gunicorn: app:app
app = create_app()

if __name__ == "__main__":
    # Solo para desarrollo local
    app.run(debug=True)