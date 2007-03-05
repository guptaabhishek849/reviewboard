from django import template
from django.template import resolve_variable
from django.template import TemplateSyntaxError, VariableDoesNotExist
from django.template.defaultfilters import capfirst
import datetime, time

register = template.Library()

class BoxNode(template.Node):
    def __init__(self, nodelist, classname):
        self.nodelist = nodelist
        self.classname = classname

    def render(self, context):
        output = "<div class=\"box-container\">"
        output += "<div class=\"box"
        if self.classname:
            output += " " + self.classname

        output += "\">\n"
        output += "<div class=\"box-inner\">"
        output += self.nodelist.render(context)

        output += "</div>"
        output += "</div>"
        output += "</div>\n"
        return output

    def render_title_area(self, context):
        return ""

@register.tag
def box(parser, token):
    classname = None

    if len(token.contents.split()) > 1:
        try:
            tag_name, classname = token.split_contents()
        except ValueError:
            raise template.TemplateSyntaxError, \
                "%r tag requires a class name" % tagname

    nodelist = parser.parse(('endbox'),)
    parser.delete_first_token()
    return BoxNode(nodelist, classname)


class ErrorBoxNode(template.Node):
    def __init__(self, nodelist, tagid):
        self.nodelist = nodelist
        self.tagid = tagid

    def render(self, context):
        output = "<div class=\"errorbox\""
        if self.tagid:
            output += " id=\"%s\"" % self.tagid

        output += ">\n"
        output += self.nodelist.render(context)
        output += "</div>"
        return output

@register.tag
def errorbox(parser, token):
    bits = token.contents.split()
    tagname = bits[0]

    if len(bits) > 1:
        raise TemplateSyntaxError, \
            "%r tag takes zero or one arguments." % tagname

    if len(bits) == 2:
        tagid = bits[1]
    else:
        tagid = None

    nodelist = parser.parse(('end' + tagname,))
    parser.delete_first_token()
    return ErrorBoxNode(nodelist, tagid)


class FormField(template.Node):
    def __init__(self, elementid):
        self.elementid = elementid

    def render(self, context):
        formelement = "form.%s" % self.elementid
        try:
            field_str = resolve_variable(formelement, context)
        except VariableDoesNotExist:
            raise template.TemplateSyntaxError, \
                "Invalid element ID %s passed to formfield tag." % formelement

        label = capfirst(self.elementid.replace('_', ' '))

        try:
            error_list = resolve_variable("%s.html_error_list" % formelement,
                                          context)
        except VariableDoesNotExist:
            error_list = ""

        output  = "  <tr>\n"
        output += "   <td class=\"label\"><label for=\"id_%s\">%s:" \
                  "</label></td>\n" % (self.elementid, label)
        output += "   <td class=\"field\">%s</td>\n" % field_str
        output += "   <td>%s</td>\n" % error_list
        output += "  </tr>\n"
        return output

@register.tag
def formfield(parser, token):
    try:
        tag_name, elementid = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, \
            "%r tag requires an element ID and a string label"

    return FormField(elementid)


class AgeId(template.Node):
    def __init__(self, timestamp):
        self.timestamp = timestamp

    def render(self, context):
        try:
            timestamp = resolve_variable(self.timestamp, context)
        except VariableDoesNotExist:
            raise template.TemplateSyntaxError, \
                "Invalid element ID %s passed to ageid tag." % self.timestamp

        # Convert datetime.date into datetime.datetime
        if timestamp.__class__ is not datetime.datetime:
            timestamp = datetime.datetime(timestamp.year, timestamp.month,
                                          timestamp.day)


        now = datetime.datetime.now()
        delta = now - (timestamp -
                       datetime.timedelta(0, 0, timestamp.microsecond))

        if delta.days == 0:
            return "age1"
        elif delta.days == 1:
            return "age2"
        elif delta.days == 2:
            return "age3"
        elif delta.days == 3:
            return "age4"
        else:
            return "age5"

@register.tag
def ageid(parser, token):
    try:
        tag_name, timestamp = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, \
            "%r tag requires a timestamp"

    return AgeId(timestamp)


@register.filter
def escapespaces(value):
    return value.replace('  ', '&nbsp; ').replace('\n', '<br />')


@register.filter
def humanize_list(value):
    if len(value) == 0:
        return ""
    elif len(value) == 1:
        return value[0]

    s = ", ".join(value[:-1])

    if len(value) > 3:
        s += ","

    return s + " and " + value[-1]


@register.filter
def indent(value, numspaces=4):
    indent_str = " " * numspaces
    return indent_str + value.replace("\n", "\n" + indent_str)
