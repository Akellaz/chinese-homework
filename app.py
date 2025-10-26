# app.py
from flask import Flask, redirect, url_for
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'chinese-homework-secret'
    
    from routes.chinese import chinese_bp
    app.register_blueprint(chinese_bp, url_prefix='/chinese')
    
    # Корневой маршрут — перенаправление на /chinese
    @app.route('/')
    def index():
        return redirect(url_for('chinese.index'))
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
