from app.models import Course, Review


class CourseRepository:
    def __init__(self, db):
        self.db = db

    def _all_query(self, name, category_ids):
        query = self.db.select(Course)

        if name:
            query = query.filter(Course.name.ilike(f'%{name}%'))

        if category_ids:
            query = query.filter(Course.category_id.in_(category_ids))

        return query

    def get_pagination_info(self, name=None, category_ids=None):
        query = self._all_query(name, category_ids)
        return self.db.paginate(query)

    def get_all_courses(self, name=None, category_ids=None, pagination=None):
        if pagination is not None:
            return pagination.items 
        
        return self.db.session.execute(self._all_query(name, category_ids)).scalars()

    def get_course_by_id(self, course_id):
        return self.db.session.get(Course, course_id)
    
    def new_course(self):
        return Course()

    def add_course(self, author_id, name, category_id, short_desc, full_desc, background_image_id):
        course = Course(
            author_id=author_id,
            name=name,
            category_id=category_id,
            short_desc=short_desc,
            full_desc=full_desc,
            background_image_id=background_image_id
        )
        try:
            self.db.session.add(course)
            self.db.session.commit()
        except Exception as e:
            self.db.session.rollback()
            raise e  # Пробрасываем любое другое исключение
        
        return course

    def get_user_review_for_course(self, course_id, user_id):
        """Проверяет, оставлял ли пользователь отзыв на этот курс"""
        from app.models import Review
        return self.db.session.execute(
            self.db.select(Review).where(
                Review.course_id == course_id,
                Review.user_id == user_id
            )
        ).scalar()

    def add_review(self, course_id, user_id, rating, text):
        """Добавляет новый отзыв"""
        from app.models import Review
        review = Review(
            course_id=course_id,
            user_id=user_id,
            rating=rating,
            text=text
        )
        try:
            self.db.session.add(review)
            self.db.session.commit()
            # Обновляем рейтинг курса
            self.update_rating(course_id, rating)
        except Exception as e:
            self.db.session.rollback()
            raise e
        return review

    def update_rating(self, course_id, new_rating):
        """Обновляет рейтинг курса после добавления отзыва"""
        course = self.get_course_by_id(course_id)
        if course:
            course.rating_sum += new_rating
            course.rating_num += 1
            try:
                self.db.session.commit()
            except Exception as e:
                self.db.session.rollback()
                raise e
        return course

    def get_reviews_with_pagination(self, course_id, page=1, per_page=10, sort_by='newest'):
        """Получает отзывы с пагинацией и сортировкой"""
        from app.models import Review
        query = self.db.select(Review).where(Review.course_id == course_id)

        if sort_by == 'newest':
            query = query.order_by(Review.created_at.desc())
        elif sort_by == 'positive_first':
            query = query.order_by(Review.rating.desc(), Review.created_at.desc())
        elif sort_by == 'negative_first':
            query = query.order_by(Review.rating.asc(), Review.created_at.desc())

        return self.db.paginate(query, page=page, per_page=per_page)

