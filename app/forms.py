from flask_wtf import FlaskForm
from wtforms import StringField, FieldList, SelectField, SelectMultipleField, BooleanField, FloatField, IntegerField
from wtforms.validators import DataRequired, Optional
from app import app


class SearchForm(FlaskForm):
    query = StringField('query', validators=[DataRequired()])


class QualityForm(FlaskForm):
    quality = SelectMultipleField('Search Quality', choices=app.config.get('AVAILABLE_QUALITIES'), validators=[Optional()])


class TVSettingsForm(QualityForm):
    pass


class MovieSettingsForm(QualityForm):
    pass


class SettingsForm(QualityForm):
    @classmethod
    def factory(cls, data, **kwargs):
        for d in data:
            if d.key != 'default_search_quality':
                if d.type == 'string':
                    setattr(cls, d.key, StringField(d.name, default=d.value))
                elif d.type == 'bool':
                    setattr(cls, d.key, BooleanField(d.name, default=d.value))
                elif d.type == 'float':
                    setattr(cls, d.key, FloatField(d.name, default=d.value))
                elif d.type == 'int':
                    setattr(cls, d.key, IntegerField(d.name, default=d.value))
        return cls(**kwargs)
