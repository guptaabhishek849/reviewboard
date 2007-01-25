from django import template
from django.template import resolve_variable
from django.template import TemplateSyntaxError, VariableDoesNotExist
from reviewboard.reviews.models import ReviewRequestDraft

register = template.Library()

class ReviewSummary(template.Node):
    def __init__(self, review_request):
        self.review_request = review_request

    def render(self, context):
        try:
            review_request = resolve_variable(self.review_request, context)
        except VariableDoesNotExist:
            raise template.TemplateSyntaxError, \
                "Invalid variable %s passed to reviewsummary tag." % \
                self.review_request

        if review_request.submitter == context.get('user', None):
            try:
                draft = review_request.reviewrequestdraft_set.get()
                return "<span class=\"draftlabel\">[Draft]</span> " + \
                       draft.summary
            except ReviewRequestDraft.DoesNotExist:
                pass

        return review_request.summary


@register.tag
def reviewsummary(parser, token):
    try:
        tag_name, review_request = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, \
            "%r tag requires a timestamp"

    return ReviewSummary(review_request)
