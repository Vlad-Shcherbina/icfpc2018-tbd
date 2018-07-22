import flask.globals
import flask.templating


_compiled_templates = {}


def memoized_render_template_string(source, **context):
    '''Same as flask.render_template_string(), but does not recompile.'''
    ctx = flask.globals._app_ctx_stack.top
    ctx.app.update_template_context(context)
    jinja_env = ctx.app.jinja_env
    k = jinja_env, source
    if k in _compiled_templates:
        template = _compiled_templates[k]
    else:
        template = _compiled_templates[k] = jinja_env.from_string(source)
    return flask.templating._render(template, context, ctx.app)
