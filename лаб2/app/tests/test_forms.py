import pytest
from app import app as test_app


@pytest.fixture
def client():
    """Фикстура для тестового клиента"""
    return test_app.test_client()


@pytest.fixture
def client_with_cookie(client):
    """Фикстура для клиента с установленным cookie"""
    client.post('/cookie', data={'action': 'set'})
    return client


# ========== ТЕСТЫ ДЛЯ СТРАНИЦЫ "ПАРАМЕТРЫ URL" ==========
# Проверка доступности страницы параметров URL
def test_url_params_page(client):
    response = client.get('/url-params')
    assert response.status_code == 200


# Cообщение об отсутствии параметров URL
def test_url_params_displays(client):
    """"""
    response = client.get('/url-params')
    assert response.status_code == 200
    assert 'Параметры URL отсутствуют' in response.text or 'Параметры URL' in response.text


# При передаче одного параметра он отображается на странице
def test_url_params_displays_single_parameter(client):
    response = client.get('/url-params?name=Иван')
    assert response.status_code == 200
    assert 'name' in response.text
    assert 'Иван' in response.text


# При передаче нескольких параметров все они отображаются на странице
def test_url_params_multiple(client):
    response = client.get('/url-params?name=Иван&age=25&city=Москва')
    assert response.status_code == 200
    assert 'name' in response.text
    assert 'Иван' in response.text
    assert 'age' in response.text
    assert '25' in response.text
    assert 'city' in response.text
    assert 'Москва' in response.text


# ========== ТЕСТЫ ДЛЯ СТРАНИЦЫ "ЗАГОЛОВКИ ЗАПРОСА" ==========
# Проверка доступности страницы заголовков запроса
def test_headers_page(client):
    response = client.get('/headers')
    assert response.status_code == 200


# Заголовок User-Agent отображается на странице
def test_headers_displays(client):
    response = client.get('/headers', headers={'User-Agent': 'TestBrowser/1.0'})
    assert response.status_code == 200
    assert 'User-Agent' in response.text
    assert 'TestBrowser/1.0' in response.text


# Заголовок Host отображается на странице
def test_headers_displays_host(client):
    response = client.get('/headers', headers={'Host': 'localhost:5000'})
    assert response.status_code == 200
    assert 'Host' in response.text


# ========== ТЕСТЫ ДЛЯ СТРАНИЦЫ "COOKIE" ==========
# Проверка доступности страницы cookie
def test_cookie(client):
    response = client.get('/cookie')
    assert response.status_code == 200


# При нажатии на кнопку установки cookie устанавливается
def test_cookie_can_be_set(client):
    response = client.post('/cookie', data={'action': 'set'})
    assert response.status_code == 200 or response.status_code == 302
    response2 = client.get('/cookie')
    assert 'Cookie установлен' in response2.text or 'существует' in response2.text


# При нажатии на кнопку удаления cookie удаляется
def test_cookie_can_be_deleted(client_with_cookie):
    client = client_with_cookie
    response = client.post('/cookie', data={'action': 'delete'})
    assert response.status_code == 200 or response.status_code == 302
    response2 = client.get('/cookie')
    assert 'Cookie не установлен' in response2.text or 'не установлен' in response2.text


# ========== ТЕСТЫ ДЛЯ СТРАНИЦЫ "ПАРАМЕТРЫ ФОРМЫ" ==========
# Проверка доступности страницы параметров формы
def test_form_params(client):
    response = client.get('/form-params')
    assert response.status_code == 200


# Страница содержит форму для ввода данных
def test_form_params_displays(client):
    response = client.get('/form-params')
    assert response.status_code == 200
    assert '<form' in response.text
    assert 'method="POST"' in response.text or 'method="post"' in response.text.lower()


# После отправки формы введённые данные отображаются на странице
def test_form_params_displays_submitted_data(client):
    response = client.post('/form-params', data={
        'name': 'Тестовый Пользователь',
        'email': 'test@example.com',
        'message': 'Тестовое сообщение',
        'option': 'option2'
    })
    assert response.status_code == 200
    assert 'Тестовый Пользователь' in response.text
    assert 'test@example.com' in response.text
    assert 'Тестовое сообщение' in response.text
    assert 'option2' in response.text


# ========== ТЕСТЫ ДЛЯ ВАЛИДАЦИИ НОМЕРА ТЕЛЕФОНА ==========
# Проверка доступности страницы  проверки телефона
def test_phone_page(client):
    response = client.get('/phone')
    assert response.status_code == 200


# Страница содержит форму, поле ввода и кнопку
def test_phone_form(client):
    response = client.get('/phone')
    assert response.status_code == 200
    assert '<form' in response.text
    assert 'name="phone"' in response.text
    assert 'Проверить' in response.text


# Валидный номер с +7 форматируется правильно
def test_phone_valid_plus7(client):
    response = client.post('/phone', data={'phone': '+7 (123) 456-75-90'})
    assert response.status_code == 200
    assert '8-123-456-75-90' in response.text
    assert 'Результат проверки' in response.text


# Валидный номер с пробелами форматируется правильно
def test_phone_valid_with_spaces_format(client):
    response = client.post('/phone', data={'phone': '+7 123 456 75 90'})
    assert response.status_code == 200
    assert '8-123-456-75-90' in response.text


# Неверное количество цифр (меньше 10)
def test_phone_invalid_wrong10(client):
    """ — сообщение об ошибке"""
    response = client.post('/phone', data={'phone': '123456789'})  # 9 цифр
    assert response.status_code == 200
    assert 'Неверное количество цифр' in response.text
    assert 'is-invalid' in response.text


# Номер с +7 но недостаточно цифр
def test_phone_invalid_wrong11(client):
    response = client.post('/phone', data={'phone': '+7 123 456 78'})  # 10 цифр с +7
    assert response.status_code == 200
    assert 'Неверное количество цифр' in response.text


# Слишком много цифр
def test_phone_invalid_too_many_digits(client):
    response = client.post('/phone', data={'phone': '1234567890123'})  # 13 цифр
    assert response.status_code == 200
    assert 'Неверное количество цифр' in response.text


# Недопустимые символы в номере
def test_phone_invalid_invalid(client):
    response = client.post('/phone', data={'phone': '+7 (123) 456-75-90abc'})
    assert response.status_code == 200
    assert 'недопустимые символы' in response.text.lower()
    assert 'is-invalid' in response.text


if __name__ == '__main__':
    pytest.main([__file__, '-v'])