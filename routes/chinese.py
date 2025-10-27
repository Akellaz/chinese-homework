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

    # Специальная обработка темы "Семья"
    if theme_config.get("name") == "Семья":
        # Подготовим данные
        family_words = list(data.items())  # [('爸爸', 'отец'), ...]
        chinese_to_russian = data
        russian_to_chinese = {v: k for k, v in data.items()}

        # Словарь для определения "старший/младший"
        senior_junior = {
            "哥哥": "старший брат", "姐姐": "старшая сестра",
            "弟弟": "младший брат", "妹妹": "младшая сестра"
        }
        senior_terms = {"哥哥", "姐姐"}
        junior_terms = {"弟弟", "妹妹"}

        # Генерируем задания
        for i in range(count):
            if i == count - 1:  # Последнее — творческое
                exercises.append("Напиши 2–3 предложения о своей семье на китайском языке. Используй слова: 爸爸, 妈妈 и одно слово из: 哥哥/姐姐/弟弟/妹妹.")
                break

            task_type = random.choices(
                ["translate", "context_fill", "choose_senior_junior", "correct_mistake"],
                weights=[4, 3, 2, 1]  # чаще — перевод и контекст
            )[0]

            if task_type == "translate":
                chinese, russian = random.choice(family_words)
                if random.choice([True, False]):
                    exercises.append(f"Переведи на русский: {chinese} → ______")
                else:
                    exercises.append(f"Напиши по-китайски: {russian} → ______")

            elif task_type == "context_fill":
                # Выбираем ребёнка из семьи
                child_word, child_meaning = random.choice(list(senior_junior.items()))
                gender = "брат" if "брат" in child_meaning else "сестра"
                age_relation = "старше" if child_word in senior_terms else "младше"

                exercises.append(
                    f"У меня есть {child_meaning}. Значит, он/она {age_relation} меня. Напиши это по-китайски: ______"
                )

            elif task_type == "choose_senior_junior":
                # Генерируем ситуацию
                name = random.choice(["Ли Миня", "Аню", "Таню", "Ваню"])
                sibling_type = random.choice(["брат", "сестра"])
                relation = random.choice(["старше", "младше"])
                
                # Определяем правильный вариант
                if sibling_type == "брат":
                    correct = "哥哥" if relation == "старше" else "弟弟"
                    wrong = "弟弟" if relation == "старше" else "哥哥"
                else:
                    correct = "姐姐" if relation == "старше" else "妹妹"
                    wrong = "妹妹" if relation == "старше" else "姐姐"

                options = [correct, wrong]
                random.shuffle(options)
                exercises.append(
                    f"У {name} есть {relation} {sibling_type}. Как это будет по-китайски?\n"
                    f"  □ {options[0]}\n"
                    f"  □ {options[1]}"
                )

            elif task_type == "correct_mistake":
                # Распространённая ошибка: путают старшего/младшего
                wrong_word, wrong_meaning = random.choice(list(senior_junior.items()))
                if wrong_word in senior_terms:
                    correct_word = wrong_word.replace("哥", "弟") if "哥" in wrong_word else wrong_word.replace("姐", "妹")
                else:
                    correct_word = wrong_word.replace("弟", "哥") if "弟" in wrong_word else wrong_word.replace("妹", "姐")
                
                exercises.append(
                    f"Исправь ошибку: «我有弟弟» — но на самом деле он СТАРШЕ меня. Правильно: ______"
                )

        return exercises

    # === СТАРАЯ ЛОГИКА ДЛЯ ОСТАЛЬНЫХ ТЕМ ===
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

    pdf_path = create_pdf(
        title=theme["name"],
        theory=theme["theory"],
        exercises=exercises,
        answers=None
    )
    return send_file(pdf_path, as_attachment=True)
