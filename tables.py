from flask_table import Table, Col

class URLHistoryTable(Table):
    _id = Col('ID')
    _url = Col('URL')
    _date = Col('Дата')

class tagTable(Table):
    _tag = Col('Tag')
    _count = Col('Count')
    _nested = Col('Nested')

class StatTable(Table):
    _name = Col('Name')
    _answer = Col('Answer')