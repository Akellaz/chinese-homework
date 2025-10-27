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

import random

def generate_exercises(theme_config, count=15):
    # Длинное поле для письма — 24 символа подчёркивания
    ANSWER_LINE = "________________________"

    theme_type = theme_config["type"]
    data = theme_config["data"]
    exercises = []

    # Специальная обработка темы "Семья"
    if theme_config.get("name") == "Семья":
        family_words = list(data.items())
        senior_junior = {
            "哥哥": "старший брат", "姐姐": "старшая сестра",
            "弟弟": "младший брат", "妹妹": "младшая сестра"
        }
        senior_terms = {"哥哥", "姐姐"}
        junior_terms = {"弟弟", "妹妹"}

        used_exercises = set()  # избегаем повторов

        # Генерируем все задания, кроме последнего (творческого)
        while len(exercises) < count - 1:
            task_type = random.choices(
                ["translate", "context_fill", "choose_senior_junior", "correct_mistake"],
                weights=[4, 3, 2, 1]
            )[0]

            if task_type == "translate":
                chinese, russian = random.choice(family_words)
                if random.choice([True, False]):
                    ex = f"Переведи на русский: {chinese} → {ANSWER_LINE}"
                else:
                    ex = f"Напиши по-китайски: {russian} → {ANSWER_LINE}"

            elif task_type == "context_fill":
                child_word = random.choice(list(senior_junior.keys()))
                meaning = senior_junior[child_word]
                ex = (
                    f"У меня есть {meaning}. "
                    f"Значит, он/она {'старше' if child_word in senior_terms else 'младше'} меня. "
                    f"Напиши это по-китайски: {ANSWER_LINE}"
                )

            elif task_type == "choose_senior_junior":
                name = random.choice(["Ли Миня", "Ани", "Тани", "Вани"])
                sibling_type = random.choice(["брат", "сестра"])
                is_senior = random.choice([True, False])

                if sibling_type == "брат":
                    correct = "哥哥" if is_senior else "弟弟"
                    wrong = "弟弟" if is_senior else "哥哥"
                    adj = "старший" if is_senior else "младший"
                else:
                    correct = "姐姐" if is_senior else "妹妹"
                    wrong = "妹妹" if is_senior else "姐姐"
                    adj = "старшая" if is_senior else "младшая"

                options = [correct, wrong]
                random.shuffle(options)
                ex = (
                    f"У {name} есть {adj} {sibling_type}. Как это будет по-китайски?\n"
                    f"  □ {options[0]}\n"
                    f"  □ {options[1]}"
                )

            elif task_type == "correct_mistake":
                ex = (
                    "Исправь ошибку: «我有弟弟» — но на самом деле он СТАРШЕ меня. "
                    f"Правильно: {ANSWER_LINE}"
                )

            # Добавляем только уникальные задания
            if ex not in used_exercises:
                used_exercises.add(ex)
                exercises.append(ex)

        # Творческое задание — всегда последнее, без поля для ответа
        exercises.append(
            "Напиши 2–3 предложения о своей семье на китайском языке.\n"
            "Используй слова: 爸爸, 妈妈 и одно из: 哥哥, 姐姐, 弟弟, 妹妹."
        )
        return exercises

    # === СТАНДАРТНАЯ ЛОГИКА ДЛЯ ОСТАЛЬНЫХ ТЕМ ===
    if theme_type == "vocabulary":
        pairs = list(data.items())
        for _ in range(count):
            chinese, russian = random.choice(pairs)
            if random.choice([True, False]):
                exercises.append(f"Переведи: {russian} → {ANSWER_LINE}")
            else:
                exercises.append(f"Напиши по-русски: {chinese} → {ANSWER_LINE}")

    elif theme_type == "grammar":
        pairs = list(data.items())
        for _ in range(count):
            chinese, russian = random.choice(pairs)
            if random.choice([True, False]):
                exercises.append(f"Переведи: {russian} → {ANSWER_LINE}")
            else:
                exercises.append(f"Составь фразу: {chinese} → {ANSWER_LINE}")

    elif theme_type == "numbers":
        numbers = list(data.keys())
        for _ in range(count):
            num = random.choice(numbers)
            chinese = data[num]
            if random.choice([True, False]):
                exercises.append(f"Напиши по-китайски: {num} → {ANSWER_LINE}")
            else:
                exercises.append(f"Напиши цифру: {chinese} → {ANSWER_LINE}")

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
    
    # Теория + словарик (если есть)
    pdf.set_font("NotoSansTC", size=12)
    for line in theory:
        pdf.multi_cell(w=0, h=7, text=line)
    pdf.ln(5)
    
    # Упражнения
    for i, ex in enumerate(exercises, 1):
        pdf.multi_cell(w=0, h=8, text=f"{i}. {ex}")
        pdf.ln(2)

    # Ответы (если понадобятся позже)
    if answers:
        pdf.add_page()
        pdf.set_font("NotoSansTC", size=14)
        pdf.cell(0, 10, "Ответы (для учителя)", new_x="LMARGIN", new_y="NEXT", align='C')
        pdf.ln(5)
        for i, ans in enumerate(answers, 1):
            pdf.multi_cell(w=0, h=8, text=f"{i}. {ans}")
            pdf.ln(2)

    filename = f"{title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    import tempfile
    filepath = os.path.join(tempfile.gettempdir(), filename)
    os.makedirs('temp', exist_ok=True)
    pdf.output(filepath)
    return filepath



# ==================== МАРШРУТЫ ====================

@chinese_bp.route('/')
def index():
    return render_template('chinese/index.html', themes=THEMES)

@chinese_bp.route('/<theme_id>')
def theme_page(theme_id):
    if theme_id not in THEMES:
        return "Тема не найдена", 404
    return render_template('chinese/module.html', theme_id=theme_id, theme=THEMES[theme_id])

@chinese_bp.route('/generate_pdf/<theme_id>', methods=['POST'])
def generate_pdf_route(theme_id):
    if theme_id not in THEMES:
        return "Тема не найдена", 404

    count = int(request.form.get('count', 15))
    theme = THEMES[theme_id]
    exercises = generate_exercises(theme, count)

    # === ДОБАВЛЯЕМ СЛОВАРИК В ТЕОРИЮ, ЕСЛИ ЭТО VOCABULARY ===
    full_theory = theme["theory"].copy()  # копируем, чтобы не менять оригинал

    if theme["type"] == "vocabulary":
        full_theory.append("")  # пустая строка как разделитель
        full_theory.append("Словарик:")
        for chinese, russian in theme["data"].items():
            full_theory.append(f"{chinese} — {russian}")

    pdf_path = create_pdf(
        title=theme["name"],
        theory=full_theory,
        exercises=exercises,
        answers=None
    )
    return send_file(pdf_path, as_attachment=True)
