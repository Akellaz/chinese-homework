import os
import random
from datetime import datetime
from flask import Blueprint, render_template, request, send_file
from fpdf import FPDF

from .themes import THEMES

chinese_bp = Blueprint('chinese', __name__, template_folder='../templates/chinese')


# ==================== ГЕНЕРАТОР УПРАЖНЕНИЙ ДЛЯ ВСЕХ ТЕМ ====================

def generate_exercises(theme_config, count=15):
    ANSWER_LINE = "____________"  # 12 символов — безопасно для FPDF

    theme_type = theme_config["type"]
    raw_data = theme_config["data"]
    # Фильтруем пустые/некорректные пары
    data_pairs = [(k, v) for k, v in raw_data.items() if k and v and str(k).strip() and str(v).strip()]
    exercises = []

    if not data_pairs:
        return [f"{i}. Данные недоступны" for i in range(1, count + 1)]

    # Специальная логика для "Семьи"
    if theme_config.get("name") == "Семья":
        senior_junior = {
            "哥哥": "старший брат", "姐姐": "старшая сестра",
            "弟弟": "младший брат", "妹妹": "младшая сестра"
        }
        senior_terms = {"哥哥", "姐姐"}
        used = set()

        while len(exercises) < count - 1:
            task_type = random.choices(
                ["translate", "context_fill", "choose_senior_junior", "correct_mistake"],
                weights=[4, 3, 2, 1]
            )[0]

            try:
                if task_type == "translate":
                    ch, ru = random.choice(data_pairs)
                    ex = f"Переведи на русский: {ch} → {ANSWER_LINE}" if random.choice([True, False]) \
                        else f"Напиши по-китайски: {ru} → {ANSWER_LINE}"
                elif task_type == "context_fill":
                    word = random.choice(list(senior_junior.keys()))
                    meaning = senior_junior[word]
                    rel = "старше" if word in senior_terms else "младше"
                    ex = f"У меня есть {meaning}. Значит, он/она {rel} меня. Напиши это по-китайски: {ANSWER_LINE}"
                elif task_type == "choose_senior_junior":
                    name = random.choice(["Ли Миня", "Ани", "Тани", "Вани"])
                    sib = random.choice(["брат", "сестра"])
                    is_senior = random.choice([True, False])
                    if sib == "брат":
                        corr = "哥哥" if is_senior else "弟弟"
                        wrong = "弟弟" if is_senior else "哥哥"
                        adj = "старший" if is_senior else "младший"
                    else:
                        corr = "姐姐" if is_senior else "妹妹"
                        wrong = "妹妹" if is_senior else "姐姐"
                        adj = "старшая" if is_senior else "младшая"
                    opts = [corr, wrong]
                    random.shuffle(opts)
                    ex = f"У {name} есть {adj} {sib}. Как это будет по-китайски?\n  □ {opts[0]}\n  □ {opts[1]}"
                elif task_type == "correct_mistake":
                    ex = f"Исправь ошибку: «我有弟弟» — но на самом деле он СТАРШЕ меня. Правильно: {ANSWER_LINE}"

                if ex and len(ex) < 200 and ex not in used:
                    used.add(ex)
                    exercises.append(ex)
            except:
                continue

        exercises.append(
            "Напиши 2–3 предложения о своей семье на китайском языке.\n"
            "Используй слова: 爸爸, 妈妈 и одно из: 哥哥, 姐姐, 弟弟, 妹妹."
        )
        return exercises

    # === УНИВЕРСАЛЬНАЯ ЛОГИКА ДЛЯ ВСЕХ ОСТАЛЬНЫХ ТЕМ ===
    for _ in range(count):
        chinese, russian = random.choice(data_pairs)
        if theme_type == "vocabulary":
            ex = f"Переведи: {russian} → {ANSWER_LINE}" if random.choice([True, False]) \
                else f"Напиши по-русски: {chinese} → {ANSWER_LINE}"
        elif theme_type == "grammar":
            ex = f"Переведи: {russian} → {ANSWER_LINE}" if random.choice([True, False]) \
                else f"Составь фразу: {chinese} → {ANSWER_LINE}"
        elif theme_type == "numbers":
            # Для чисел: данные — это {число: иероглиф}
            num = random.choice(list(raw_data.keys()))
            ch_num = raw_data[num]
            ex = f"Напиши по-китайски: {num} → {ANSWER_LINE}" if random.choice([True, False]) \
                else f"Напиши цифру: {ch_num} → {ANSWER_LINE}"
        else:
            ex = f"Задание: {chinese} → {ANSWER_LINE}"

        if ex and len(ex) < 250:
            exercises.append(ex)

    return exercises[:count]


# ==================== PDF ГЕНЕРАТОР (СТАБИЛЬНЫЙ) ====================

class ChinesePDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_margins(left=15, top=20, right=15)
        self.set_auto_page_break(auto=True, margin=20)
        font_path = os.path.join(os.path.dirname(__file__), '..', 'fonts', 'NotoSansTC-Regular.ttf')
        if not os.path.exists(font_path):
            raise RuntimeError(f"Шрифт не найден: {font_path}")
        self.add_font("NotoSansTC", fname=font_path)
        self.set_font("NotoSansTC", size=12)

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
    pdf.cell(pdf.epw, 10, title, new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(8)

    # Теория
    pdf.set_font("NotoSansTC", size=12)
    for line in theory:
        text = str(line).strip() if line else ""
        pdf.multi_cell(w=pdf.epw, h=7, text=text)
    pdf.ln(5)

    # Упражнения
    for i, ex in enumerate(exercises, 1):
        pdf.set_font("NotoSansTC", size=12)
        pdf.multi_cell(w=pdf.epw, h=8, text=f"{i}. {ex}")
        pdf.ln(2)

    # Ответы (если понадобятся)
    if answers:
        pdf.add_page()
        pdf.set_font("NotoSansTC", size=14)
        pdf.cell(pdf.epw, 10, "Ответы (для учителя)", new_x="LMARGIN", new_y="NEXT", align='C')
        pdf.ln(5)
        for i, ans in enumerate(answers, 1):
            pdf.multi_cell(w=pdf.epw, h=8, text=f"{i}. {ans}")
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

    # Передаём ТОЛЬКО оригинальную теорию (без словарика)
    pdf_path = create_pdf(
        title=theme["name"],
        theory=theme["theory"],
        exercises=exercises,
        answers=None
    )
    return send_file(pdf_path, as_attachment=True)