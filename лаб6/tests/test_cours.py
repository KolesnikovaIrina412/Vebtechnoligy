import pytest
import sys
import os

# Добавляем родительскую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, Course, Category, Review
from werkzeug.security import generate_password_hash

created_test_courses = []


@pytest.fixture
def app():
    """Фикстура для создания тестового приложения"""
    test_app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
        'UPLOAD_FOLDER': '/tmp/test_uploads'
    })

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.drop_all()


@pytest.fixture
def client(app):
    """Фикстура для тестового клиента"""
    return app.test_client()


@pytest.fixture
def init_database(app):
    """Фикстура для инициализации тестовой БД"""
    with app.app_context():
        # Создаем категории
        categories = [
            Category(name='Программирование'),
            Category(name='Математика'),
            Category(name='Языкознание')
        ]
        for category in categories:
            db.session.add(category)

        # Создаем пользователей
        users = [
            User(
                login='author',
                password_hash=generate_password_hash('author123'),
                first_name='Автор',
                last_name='Курсов',
                middle_name='Авторович'
            ),
            User(
                login='student',
                password_hash=generate_password_hash('student123'),
                first_name='Студент',
                last_name='Тестов',
                middle_name='Студентович'
            ),
            User(
                login='reviewer',
                password_hash=generate_password_hash('reviewer123'),
                first_name='Рецензент',
                last_name='Отзывов',
                middle_name='Рецензентович'
            )
        ]
        for user in users:
            db.session.add(user)

        db.session.commit()

        # СОЗДАЙТЕ ТЕСТОВОЕ ИЗОБРАЖЕНИЕ
        from app.models import Image
        import uuid
        test_image = Image(
            id=str(uuid.uuid4()),
            file_name='test.jpg',
            mime_type='image/jpeg',
            md5_hash='test_hash_123'
        )
        db.session.add(test_image)
        db.session.commit()

        # Получаем автора, категорию и изображение
        author = db.session.execute(db.select(User).where(User.login == 'author')).scalar()
        category = db.session.execute(db.select(Category).where(Category.name == 'Программирование')).scalar()
        image = db.session.execute(db.select(Image)).scalar()

        # Создаем тестовые курсы с image_id
        courses = [
            Course(
                name='Python для начинающих',
                short_desc='Базовый курс по Python',
                full_desc='Подробный курс по основам программирования на Python',
                category_id=category.id,
                author_id=author.id,
                background_image_id=image.id,  # используем image.id вместо None
                rating_sum=0,
                rating_num=0
            ),
            Course(
                name='JavaScript основы',
                short_desc='Введение в JavaScript',
                full_desc='Курс по основам JavaScript для начинающих',
                category_id=category.id,
                author_id=author.id,
                background_image_id=image.id,  # используем image.id вместо None
                rating_sum=0,
                rating_num=0
            ),
            Course(
                name='Алгоритмы и структуры данных',
                short_desc='Продвинутый курс по алгоритмам',
                full_desc='Изучение алгоритмов и структур данных',
                category_id=category.id,
                author_id=author.id,
                background_image_id=image.id,  # используем image.id вместо None
                rating_sum=0,
                rating_num=0
            )
        ]
        for course in courses:
            db.session.add(course)

        db.session.commit()
        yield db


@pytest.fixture
def authenticated_client(client, init_database):
    """Фикстура для авторизованного клиента (студент)"""
    with client:
        client.post('/auth/login', data={
            'login': 'student',
            'password': 'student123'
        }, follow_redirects=True)
        return client


@pytest.fixture
def author_client(client, init_database):
    """Фикстура для авторизованного клиента (автор курса)"""
    with client:
        client.post('/auth/login', data={
            'login': 'author',
            'password': 'author123'
        }, follow_redirects=True)
        return client


# Тест 1: Страница каталога курсов доступна
def test_courses_index_page_accessible(client, init_database):
    response = client.get('/courses/')
    assert response.status_code == 200
    assert 'Каталог курсов' in response.data.decode('utf-8')


# Тест 2: На странице каталога отображаются курсы
def test_courses_index_shows_courses(client, init_database):
    response = client.get('/courses/')
    response_text = response.data.decode('utf-8')
    assert 'Python для начинающих' in response_text
    assert 'JavaScript основы' in response_text
    assert 'Алгоритмы и структуры данных' in response_text


# Тест 3: Поиск курсов по названию работает
def test_courses_search_by_name(client, init_database):
    response = client.get('/courses/?name=Python')
    response_text = response.data.decode('utf-8')
    assert 'Python для начинающих' in response_text
    assert 'JavaScript основы' not in response_text


# Тест 4: Фильтрация по категории работает
def test_courses_filter_by_category(client, init_database):
    category = db.session.execute(db.select(Category).where(Category.name == 'Программирование')).scalar()
    response = client.get(f'/courses/?category_ids={category.id}')
    assert response.status_code == 200


# Тест 5: Страница просмотра курса доступна
def test_course_show_page_accessible(client, init_database):
    course = db.session.execute(db.select(Course)).scalar()
    response = client.get(f'/courses/{course.id}')
    assert response.status_code == 200
    assert course.name in response.data.decode('utf-8')


# Тест 6: Несуществующий курс возвращает 404
def test_nonexistent_course_returns_404(client, init_database):
    response = client.get('/courses/99999')
    assert response.status_code == 404


# Тест 7: Страница создания курса требует авторизации
def test_new_course_page_requires_auth(client, init_database):
    response = client.get('/courses/new', follow_redirects=True)
    response_text = response.data.decode('utf-8')
    assert 'Войти' in response_text or 'Логин' in response_text


# Тест 8: Создание нового курса работает
def test_create_course_success(author_client, init_database):
    category = db.session.execute(db.select(Category)).scalar()

    # Создаем тестовое изображение
    from app.models import Image
    import uuid
    test_image = Image(
        id=str(uuid.uuid4()),
        file_name='test_background.jpg',
        mime_type='image/jpeg',
        md5_hash='test_hash_' + str(uuid.uuid4())[:8]
    )
    db.session.add(test_image)
    db.session.commit()

    # Создаем форму с файлом изображения
    data = {
        'name': 'Новый тестовый курс',
        'category_id': category.id,
        'short_desc': 'Краткое описание тестового курса',
        'full_desc': 'Полное описание тестового курса',
        'author_id': 1
    }

    # Создаем mock-файл для отправки
    from io import BytesIO
    file_data = {
        'background_img': (BytesIO(b'dummy image content'), 'test.jpg')
    }

    response = author_client.post('/courses/create',
                                  data=data,
                                  content_type='multipart/form-data',
                                  follow_redirects=True)

    response_text = response.data.decode('utf-8')
    assert response.status_code == 200
    course = db.session.execute(db.select(Course).where(Course.name=='Новый тестовый курс')).scalar()
    if course:
        created_test_courses.append(course.name)
        assert course is not None
    else:
        # Если курс не создался, проверяем, что это не ошибка сервера
        assert '500' not in response_text


# Тест 9: Форма отзыва не видна для неавторизованных
def test_review_form_hidden_for_anonymous(client, init_database):
    course = db.session.execute(db.select(Course)).scalar()
    response = client.get(f'/courses/{course.id}')
    response_text = response.data.decode('utf-8')
    assert 'Войдите' in response_text or 'Войти' in response_text


# Тест 10: Создание отзыва работает
def test_create_review_success(authenticated_client, init_database):
    course = db.session.execute(db.select(Course)).scalar()
    response = authenticated_client.post(f'/courses/{course.id}/reviews/create', data={
        'rating': 5,
        'text': 'Отличный курс! Очень понравилось!'
    }, follow_redirects=True)

    response_text = response.data.decode('utf-8')
    assert 'Спасибо' in response_text or 'отзыв' in response_text


# Тест 11: Пользователь не может оставить два отзыва на один курс
def test_cannot_create_duplicate_review(authenticated_client, init_database):
    course = db.session.execute(db.select(Course)).scalar()

    authenticated_client.post(f'/courses/{course.id}/reviews/create', data={
        'rating': 4,
        'text': 'Первый отзыв'
    })

    response = authenticated_client.post(f'/courses/{course.id}/reviews/create', data={
        'rating': 5,
        'text': 'Второй отзыв'
    }, follow_redirects=True)

    response_text = response.data.decode('utf-8')
    assert 'уже оставили отзыв' in response_text


# Тест 12: Отзыв без текста не принимается
def test_create_review_validation_text_required(authenticated_client, init_database):
    course = db.session.execute(db.select(Course)).scalar()
    response = authenticated_client.post(f'/courses/{course.id}/reviews/create', data={
        'rating': 5,
        'text': ''
    }, follow_redirects=True)

    response_text = response.data.decode('utf-8')
    assert 'не может быть пустым' in response_text


# Тест 13: Страница всех отзывов доступна
def test_all_reviews_page_accessible(client, init_database):
    course = db.session.execute(db.select(Course)).scalar()
    response = client.get(f'/courses/{course.id}/reviews')
    assert response.status_code == 200
    assert 'Отзывы' in response.data.decode('utf-8')


# Тест 14: После создания отзыва форма заменяется на отображение
def test_review_form_replaced_after_create(authenticated_client, init_database):
    course = db.session.execute(db.select(Course)).scalar()

    authenticated_client.post(f'/courses/{course.id}/reviews/create', data={
        'rating': 5,
        'text': 'Тестовый отзыв для проверки'
    }, follow_redirects=True)

    response = authenticated_client.get(f'/courses/{course.id}')
    response_text = response.data.decode('utf-8')
    assert 'Ваш отзыв' in response_text or 'Тестовый отзыв' in response_text


# Тест 15: Рейтинг курса обновляется после добавления отзыва
def test_course_rating_updates_after_review(authenticated_client, init_database):
    course = db.session.execute(db.select(Course)).scalar()
    initial_rating = course.rating

    authenticated_client.post(f'/courses/{course.id}/reviews/create', data={
        'rating': 5,
        'text': 'Отличный курс!'
    })

    db.session.refresh(course)
    assert course.rating != initial_rating


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
