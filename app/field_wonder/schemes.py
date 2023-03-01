from marshmallow import Schema, fields


class GameSchema(Schema):
    id = fields.Int()
    question = fields.Nested("QuestionGameSchema")
    players = fields.Nested("PlayerSchema", many=True)


class QuestionGameSchema(Schema):
    id = fields.Int()
    description = fields.Str()
    answer = fields.Str()


class PlayerSchema(Schema):
    id = fields.Int()
    user = fields.Pluck("UserTG", "username")
    score = fields.Int()


class UserTG(Schema):
    id = fields.Int()
    username = fields.Str()
