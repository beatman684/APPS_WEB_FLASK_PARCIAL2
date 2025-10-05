# APPS WEB FLASK PARCIAL 2

Proyecto base en Flask con plantillas dinámicas (Jinja2) para cumplir la tarea del parcial.

## Estructura
```
APPS_WEB_FLASK_PARCIAL2/
├── app.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── about.html
├── static/
│   └── styles.css
├── requirements.txt
├── .gitignore
└── render.yaml
```

## Requisitos
- Python 3.10+

## Desarrollo local
```bash
# 1) Crear y activar entorno
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
# source venv/bin/activate

# 2) Instalar dependencias
pip install -r requirements.txt

# 3) Ejecutar en desarrollo
python app.py
# o: flask --app app run --debug
```

Visita: http://localhost:5000

## Despliegue en Render
Este repo incluye `render.yaml` con:
- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app`

Pasos en https://render.com:
1. Crear nuevo **Web Service** y conectar el repo.
2. Plan: Free.
3. Aceptar el `render.yaml` detectado automáticamente o configurarlo manualmente.
4. Deploy.