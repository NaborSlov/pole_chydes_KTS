from marshmallow import Schema, fields


class AdminSchema(Schema):
    id = fields.Int(required=False)
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)


class QuestionSchema(Schema):
    id = fields.Int()
    description = fields.Str(required=True)
    answer = fields.Str(required=True)


class RetrieveQuestionSchema(Schema):
    id = fields.Int()

