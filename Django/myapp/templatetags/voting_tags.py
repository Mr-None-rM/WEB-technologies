from django import template

register = template.Library()

@register.simple_tag
def get_question_vote(user_question_votes, question_id):
    return user_question_votes.get(question_id)

@register.simple_tag
def get_answer_vote(user_answer_votes, answer_id):
    return user_answer_votes.get(answer_id)