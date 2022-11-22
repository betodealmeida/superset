from flask import current_app, session
#from superset import security_manager
from superset.db_engine_specs.postgres import PostgresBaseEngineSpec
from superset.db_engine_specs.base import BasicParametersMixin


class TIPPostgresEngineSpec(PostgresBaseEngineSpec, BasicParametersMixin):
    engine = "tip"
    engine_name = "The Intertrust Platform"
    engine_aliases = {'tip'}
    default_driver = "psycopg2"
    sqlalchemy_uri_placeholder = "tip+psycopg2://{host}:{port}/tip"

    @classmethod
    def modify_url_for_impersonation(cls, url, impersonate_user, username, access_token=None):
        provider = session.get('oauth_provider')
        #user = security_manager.find_user(username=username)
        #current_app.logger.info("[TIP] impersonate user: {0}".format(user))
        current_app.logger.debug("[TIP] session.oauth_provider: {0}".format(provider))

        cur_session_access_token = current_app.appbuilder.sm.oauth_remotes[provider].token
        current_app.logger.debug("[TIP] cur_session_token: {0}".format(cur_session_access_token))
        current_app.logger.debug("[TIP] url before: {0}".format(url))
        current_app.logger.info("[TIP] impersonate_user: {0}".format(impersonate_user))
        current_app.logger.info("[TIP] access_token: {0}".format(access_token))
        current_app.logger.debug("[TIP] url before: {0}".format(url))

        if impersonate_user:
            url.username = 'authx_token'
            url.password = cur_session_access_token

        url.drivername = 'postgresql+psycopg2'
        current_app.logger.debug("[TIP] url after: {0}".format(url))


