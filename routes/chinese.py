# routes/chinese.py
import os
import random
from datetime import datetime
from flask import Blueprint, render_template, request, send_file
from fpdf import FPDF

# Импортируем темы из отдельного файла
from .themes import THEMES

chinese_bp = Blueprint('chinese', __name__, template_folder='../templates/chinese')



# ==================== УНИВЕРСАЛЬНЫЙ ГЕНЕРАТОР УПРАЖНЕНИЙ ====================

def generate_exercises(theme_config, count=15):
    theme_type = theme_config["type"]
    data = theme_config["data"]
    exercises = []

    if theme_type == "vocabulary":
        pairs = list(data.items())
        for _ in range(count):
            chinese, russian = random.choice(pairs)
            if random.choice([True, False]):
                exercises.append(f"Переведи: {russian} → ______")
            else:
                exercises.append(f"Напиши по-русски: {chinese} → ______")

    elif theme_type == "grammar":
        pairs = list(data.items())
        for _ in range(count):
            chinese, russian = random.choice(pairs)
            if random.choice([True, False]):
                exercises.append(f"Переведи: {russian} → ______")
            else:
                exercises.append(f"Составь фразу: {chinese} → ______")

    elif theme_type == "numbers":
        numbers = list(data.keys())
        for _ in range(count):
            num = random.choice(numbers)
            chinese = data[num]
            if random.choice([True, False]):
                exercises.append(f"Напиши по-китайски: {num} → ______")
            else:
                exercises.append(f"Напиши цифру: {chinese} → ______")

    return exercises[:count]

# ==================== PDF ГЕНЕРАТОР (с NotoSansTC) ====================

class ChinesePDF(FPDF):
    def __init__(self):
        super().__init__()
        font_path = os.path.join(os.path.dirname(__file__), '..', 'fonts', 'NotoSansTC-Regular.ttf')
        if not os.path.exists(font_path):
            raise RuntimeError(f"Шрифт не найден: {font_path}")
        self.add_font("NotoSansTC", fname=font_path)

    def header(self):
        self.set_font("NotoSansTC", size=14)
        self.cell(0, 10, "Китайский язык — Домашнее задание", new_x="LMARGIN", new_y="NEXT", align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("NotoSansTC", size=10)
        self.cell(0, 10, f"Сгенерировано: {datetime.now().strftime('%d.%m.%Y')}", align='C')

def create_pdf(title, theory, exercises, answers=None):
    pdf = ChinesePDF()
    pdf.add_page()
    
    # Заголовок
    pdf.set_font("NotoSansTC", size=16)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(8)
    
    # Теория
    pdf.set_font("NotoSansTC", size=12)
    for line in theory:
        pdf.multi_cell(w=190, h=8, text=line)
    pdf.ln(5)
    
    # Упражнения
    pdf.set_font("NotoSansTC", size=12)
    for i, ex in enumerate(exercises, 1):
        pdf.cell(0, 10, f"{i}. {ex}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    # Ответы (опционально)
    if answers:
        pdf.add_page()
        pdf.set_font("NotoSansTC", size=14)
        pdf.cell(0, 10, "Ответы (для учителя)", new_x="LMARGIN", new_y="NEXT", align='C')
        pdf.ln(5)
        pdf.set_font("NotoSansTC", size=12)
        for i, ans in enumerate(answers, 1):
            pdf.cell(0, 8, f"{i}. {ans}", new_x="LMARGIN", new_y="NEXT")
    
    filename = f"{title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join('temp', filename)
    os.makedirs('temp', exist_ok=True)
    pdf.output(filepath)
    return filepath



# ==================== МАРШРУТЫ ====================

@chinese_bp.route('/chinese')
def index():
    return render_template('chinese/index.html', themes=THEMES)

@chinese_bp.route('/chinese/<theme_id>')
def theme_page(theme_id):
    if theme_id not in THEMES:
        return "Тема не найдена", 404
    return render_template('chinese/module.html', theme_id=theme_id, theme=THEMES[theme_id])

@chinese_bp.route('/chinese/generate_pdf/<theme_id>', methods=['POST'])
def generate_pdf_route(theme_id):
    if theme_id not in THEMES:
        return "Тема не найдена", 404

    count = int(request.form.get('count', 15))
    theme = THEMES[theme_id]
    exercises = generate_exercises(theme, count)

    pdf_path = create_pdf(
        title=theme["name"],
        theory=theme["theory"],
        exercises=exercises,
        answers=None
    )
    return send_file(pdf_path, as_attachment=True)
