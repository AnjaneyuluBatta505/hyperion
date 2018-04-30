from flask_wtf import Form
from wtforms import StringField, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, URL, number_range


class WatcherForm(Form):

    RUN_FREQ_CHOICES = (
        ('every 5 mins', '5 mins'),
        ('every 15 mins', '15 mins'),
        ('every 30 mins', '30 mins'),
        ('every 1 hours', '1 hour'),
        ('every 3 hours', '3 hours'),
        ('every 6 hours', '6 hours'),
    )

    email = StringField('Email', validators=[DataRequired(), Email()])
    url = StringField('Password', validators=[DataRequired(), URL()])
    status_code = IntegerField(
        'Status Code',
        validators=[DataRequired(), number_range(100, 599)])
    run_freq = SelectField('Run Every', choices=RUN_FREQ_CHOICES)
