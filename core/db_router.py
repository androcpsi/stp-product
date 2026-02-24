class OracleRouter:

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'oracle_models':
            return 'oracle_prod'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'oracle_models':
            return 'oracle_prod'
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == 'oracle_prod':
            return False
        return None