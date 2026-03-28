import pytest
import re
from datetime import datetime
from app import app as test_app, posts_list as real_posts_list


@pytest.fixture
def client():
    return test_app.test_client()


@pytest.fixture
def posts_list():
    return [
        {
            'title': 'Заголовок поста',
            'text': 'Текст поста для тестирования',
            'author': 'Иванов Иван Иванович',
            'date': datetime(2025, 3, 10),
            'image_id': '123.jpg',
            'comments': [
                {
                    'author': 'Петров Петр',
                    'text': 'Отличный пост!',
                    'replies': [
                        {
                            'author': 'Александр',
                            'text': 'Согласен!'
                        }
                    ]
                }
            ]
        }
    ]


# При обращении к /posts используется шаблон posts.html
def test_posts_index_uses(client, captured_templates, mocker, posts_list):
    with captured_templates as templates:
        mocker.patch("app.posts_list", return_value=posts_list, autospec=True)
        response = client.get('/posts')
        assert response.status_code == 200
        assert len(templates) == 1
        template, context = templates[0]
        assert template.name == 'posts.html'


# При обращении к /posts/0 используется шаблон post.html
def test_post_detail_uses(client, captured_templates, mocker, posts_list):
    with captured_templates as templates:
        mocker.patch("app.posts_list", return_value=posts_list, autospec=True)
        response = client.get('/posts/0')
        assert response.status_code == 200
        assert len(templates) == 1
        template, context = templates[0]
        assert template.name == 'post.html'


# При обращении к /about используется шаблон about.html
def test_about_uses(client, captured_templates, mocker, posts_list):
    with captured_templates as templates:
        mocker.patch("app.posts_list", return_value=posts_list, autospec=True)
        response = client.get('/about')
        assert response.status_code == 200
        assert len(templates) == 1
        template, context = templates[0]
        assert template.name == 'about.html'


# В шаблон posts.html передаются данные о постах
def test_posts_list_passes_posts_data(client, captured_templates, mocker, posts_list):
    with captured_templates as templates:
        mocker.patch("app.posts_list", return_value=posts_list, autospec=True)

        client.get('/posts')
        template, context = templates[0]

        assert 'posts' in context
        assert len(context['posts']) == 1
        assert context['posts'][0]['title'] == 'Заголовок поста'


# В шаблон post.html передаются данные о конкретном посте
def test_post_detail_passes_post_data(client, captured_templates):
    with captured_templates as templates:
        client.get('/posts/0')
        template, context = templates[0]
        assert 'post' in context
        assert isinstance(context['post'], dict)
        # Проверяем наличие всех необходимых полей в посте
        expected_fields = ['title', 'text', 'author', 'date', 'image_id', 'comments']
        for field in expected_fields:
            assert field in context['post']


# В шаблон about.html передается заголовок страницы
def test_about_passes_title(client, captured_templates):
    with captured_templates as templates:
        client.get('/about')
        template, context = templates[0]
        assert 'title' in context
        assert context['title'] == 'Об авторе'


# Заголовок и автор поста отображаются на странице
def test_post_title_and_author_displayed(client):
    posts = real_posts_list()
    test_post = posts[0]
    response = client.get('/posts/0')
    assert response.status_code == 200
    assert test_post['title'] in response.text
    assert test_post['author'] in response.text


# Текст поста отображается на странице
def test_post_text_displayed(client):
    posts = real_posts_list()
    test_post = posts[0]
    text_sample = test_post['text'][:50]
    response = client.get('/posts/0')
    assert response.status_code == 200
    assert text_sample in response.text


# Присутствуют изображение поста и форма комментариев
def test_post_image_and_comments_form_present(client):
    posts = real_posts_list()
    test_post = posts[0]
    response = client.get('/posts/0')
    assert response.status_code == 200
    image_url = f'/static/images/{test_post["image_id"]}'
    assert image_url in response.text
    assert 'Оставьте комментарий' in response.text
    assert 'Отправить' in response.text
    assert '<form' in response.text
    assert 'name="text"' in response.text or 'id="commentText"' in response.text


# дата публикации поста в формате ДД.ММ.ГГГГ
def test_post_date_format_correct(client):
    posts = real_posts_list()
    test_post = posts[0]
    response = client.get('/posts/0')
    assert response.status_code == 200

    # Форматируем дату по шаблону
    expected_formats = [
        test_post['date'].strftime('%d.%m.%Y'),
        test_post['date'].strftime('%d.%m.%Y в %H:%M')
    ]

    assert any(fmt in response.text for fmt in expected_formats)


# Корректность даты
def test_date_format(client):
    response = client.get('/posts/0')
    assert response.status_code == 200
    date_pattern = r'\d{2}\.\d{2}\.\d{4}'
    dates = re.findall(date_pattern, response.text)

    # На странице должна быть хотя бы одна дата
    assert len(dates) > 0

    # Проверяем, что день и месяц в правильном диапазоне
    for date_str in dates:
        day, month, year = date_str.split('.')
        assert 1 <= int(day) <= 31
        assert 1 <= int(month) <= 12
        assert len(year) == 4


# Даты комментариев
def test_comment_date_displayed_correctly(client):
    response = client.get('/posts/0')
    assert response.status_code == 200

    # Ищем даты комментариев
    date_pattern = r'\d{2}\.\d{2}\.\d{4}'
    dates = re.findall(date_pattern, response.text)
    if 'Комментарии' in response.text:
        assert len(dates) >= 1


# Код 404 при обращении к несуществующему посту
def test_invalid_post_id_returns_404(client):
    # общее количество постов
    posts = real_posts_list()
    total_posts = len(posts)

    # доступ к посту с индексом, равным количеству постов
    response = client.get(f'/posts/{total_posts}')
    assert response.status_code == 404

    # доступ к посту с отрицательным индексом
    response = client.get('/posts/-1')
    assert response.status_code == 404


# Код 404 при обращении с нечисловым идентификатором
def test_string_post_id_returns_404(client):
    response = client.get('/posts/abc')
    assert response.status_code == 404


# Код 404 при обращении к несуществующему маршруту
def test_nonexistent_route_returns_404(client):
    response = client.get('/nonexistent-route-12345')
    assert response.status_code == 404


# Наличие футера
def test_footer_present(client):
    pages = ['/', '/posts', '/posts/0', '/about']
    expected_text = "Колесникова Ирина Владимировна 241-372"

    for page in pages:
        response = client.get(page)
        assert response.status_code == 200
        assert expected_text in response.text


# Все обязательные элементы страницы post
def test_all_required_elements_in_post_page(client):
    response = client.get('/posts/0')
    assert response.status_code == 200

    # Проверяем наличие всех обязательных элементов
    required_elements = [
        'Оставьте комментарий',
        'Отправить',
        'Комментарии'
    ]

    for element in required_elements:
        assert element in response.text
    assert '<h1' in response.text or '<h2' in response.text
    assert '<img' in response.text


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
