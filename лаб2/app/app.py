import random
import re
from flask import Flask, render_template
from faker import Faker
from flask import request, make_response, redirect, url_for

fake = Faker()

app = Flask(__name__)
application = app


def generate_comments(replies=True):
    comments = []
    for _ in range(random.randint(1, 3)):
        comment = {'author': fake.name(), 'text': fake.text()}
        if replies:
            comment['replies'] = generate_comments(replies=False)
        comments.append(comment)
    return comments


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html', title='Об авторе')


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', title='Страница не найдена'), 404


# лр2
@app.route('/url-params')
def url_params():
    # Получаем все параметры из URL (данные после ? в адресной строке)
    url_params = dict(request.args)

    return render_template(
        'url_params.html',
        title='Параметры URL',
        url_params=url_params
    )


@app.route('/headers')
def headers_info():
    # Получаем все заголовки запроса
    headers = dict(request.headers)

    return render_template(
        'headers.html',
        title='Заголовки запроса',
        headers=headers
    )


# Страница для отображения параметров формы.
@app.route('/form-params', methods=['GET', 'POST'])
def form_params():
    form_data = None
    submitted = False

    if request.method == 'POST':
        # Получаем данные из формы
        form_data = dict(request.form)
        submitted = True

    return render_template(
        'form_params.html',
        title='Параметры формы',
        form_data=form_data,
        submitted=submitted
    )


@app.route('/cookie', methods=['GET', 'POST'])
def cookie():
    # Имя нашего тестового cookie
    COOKIE_NAME = 'cookie'
    COOKIE_VALUE = 'Hello World!'

    # Получаем текущее значение cookie
    current_cookie_value = request.cookies.get(COOKIE_NAME)

    # Обработка POST-запроса (кнопки "Установить" или "Удалить")
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'set':
            # Устанавливаем cookie
            response = make_response(redirect(url_for('cookie')))
            response.set_cookie(
                COOKIE_NAME,  # имя cookie
                COOKIE_VALUE,  # значение
                max_age=3600,  # время жизни в секундах (1 час)
                httponly=True,  # защита от XSS-атак
                samesite='Lax'  # защита от CSRF
            )
            return response

        elif action == 'delete':
            # Удаляем cookie
            response = make_response(redirect(url_for('cookie')))
            response.delete_cookie(COOKIE_NAME)
            return response

    # Если cookie существует, показываем его
    return render_template(
        'cookie.html',
        title='Cookie',
        cookie_exists=current_cookie_value is not None,
        cookie_value=current_cookie_value
    )


@app.route('/phone', methods=['GET', 'POST'])
def phone():
    phone_number = ''
    error_message = None
    formatted_number = None

    if request.method == 'POST':
        phone_number = request.form.get('phone', '').strip()

        # Валидация номера телефона
        error_message = validate_phone_number(phone_number)

        if not error_message:
            # Если ошибок нет, форматируем номер
            formatted_number = format_phone_number(phone_number)

    return render_template(
        'phone.html',
        title='Проверка номера телефона',
        phone_number=phone_number,
        error_message=error_message,
        formatted_number=formatted_number
    )


def validate_phone_number(phone):
    # Сохраняем исходный номер для проверки символов
    original_phone = phone

    # Разрешенные символы: цифры, пробелы, скобки, дефисы, точки, плюс
    allowed_chars_pattern = r'^[\d\s\(\)\-\.\+]+$'

    # Проверка на недопустимые символы
    if not re.match(allowed_chars_pattern, phone):
        return "Недопустимый ввод. В номере телефона встречаются недопустимые символы."

    # Извлекаем только цифры из номера
    digits = re.sub(r'\D', '', phone)  # удаляем всё кроме цифр

    # Определяем ожидаемое количество цифр
    expected_digits = None

    # Проверка начинается ли номер с +7 или 8
    # Для этого смотрим на оригинальный номер (без удаления символов)
    phone_stripped = phone.strip()

    # Проверяем наличие +7 в начале
    if phone_stripped.startswith('+7'):
        expected_digits = 11
    # Проверяем наличие 8 в начале (с учётом что после 8 могут быть другие символы)
    elif phone_stripped.startswith('8'):
        # Извлекаем первую цифру из очищенного номера
        if digits and digits[0] == '8':
            expected_digits = 11
        else:
            expected_digits = 10
    else:
        # В остальных случаях - 10 цифр
        expected_digits = 10

    # Проверяем количество цифр
    if expected_digits == 11:
        if len(digits) != 11:
            return "Недопустимый ввод. Неверное количество цифр."
        # Дополнительная проверка: если 11 цифр, первая должна быть 7 или 8
        if digits[0] not in ['7', '8']:
            return "Недопустимый ввод. Неверное количество цифр."
    else:  # expected_digits == 10
        if len(digits) != 10:
            return "Недопустимый ввод. Неверное количество цифр."

    return None  # Номер валидный


def format_phone_number(phone):
    # Извлекаем все цифры из номера
    digits = re.sub(r'\D', '', phone)

    # Если 11 цифр и первая 7, заменяем на 8
    if len(digits) == 11 and digits[0] == '7':
        digits = '8' + digits[1:]

    # Если 11 цифр и первая 8, просто используем как есть
    if len(digits) == 11 and digits[0] == '8':
        digits = digits

    # Если 10 цифр, добавляем 8 в начало
    if len(digits) == 10:
        digits = '8' + digits

    # Форматируем: 8-***-***-**-**
    formatted = f"{digits[0]}-{digits[1:4]}-{digits[4:7]}-{digits[7:9]}-{digits[9:11]}"

    return formatted
