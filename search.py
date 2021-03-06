from fabric.api import *

import util

SEARCHABLE_APPS = {
    'calendars':             ('frontend', ['panopticon:register']),
    'designprinciples':      ('frontend', ['rummager:index']), # Includes the service-manual. Note: not included in gov.uk/search
    'frontend':              ('frontend', ['rummager:index']),
    'licencefinder':         ('frontend', ['panopticon:register']),
    'businesssupportfinder': ('frontend', ['panopticon:register']),
    'publisher':             ('backend',  ['panopticon:register']),
    'recommended-links':     ('backend',  ['rummager:index']),
    'smartanswers':          ('frontend', ['panopticon:register']),
    'tariff':                ('frontend', ['panopticon:register']),
    'travel-advice-publisher':('backend', ['panopticon:register', 'panopticon:reregister_editions']),
    'whitehall':             ('whitehall_backend',  ['rummager:index']),
}

@task
def list():
    """List known searchable applications"""

    for app in sorted(SEARCHABLE_APPS.keys()):
        puts(app)

@task
def reindex(app=None):
    """

    Rebuild search indices

    To reindex all applications, run

      fab search.reindex

    To reindex only one application, e.g. calendars, you can do

      fab search.reindex:calendars

    """

    # If no argument is given, rebuild indices for all available applications
    if app is None:
        for app in SEARCHABLE_APPS.keys():
            reindex_app(app)

    else:
        if app not in SEARCHABLE_APPS:
            abort("I don't know anything about %s. Try updating SEARCHABLE_APPS in search.py." % app)
        reindex_app(app)


def reindex_app(app):
    puts("Rebuilding search index for application '%s'" % app)

    machine_class, tasks = SEARCHABLE_APPS[app]
    util.use_random_host('class-%s' % machine_class)

    for task in tasks:
        # FIXME: Remove this horrible hack of a hack for a hack
        if app == 'recommended-links':
            with cd('/data/vhost/recommended-links.*/current'):
                sudo('govuk_setenv default bundle exec rake -v "%s" --trace' % task, user='deploy')
        else:
            util.rake(app, task)
