class MLRouter:
    def db_for_read(self, model, **hints):
        if model._meta.db_table == "lutas":
            return "ml"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.db_table == "lutas":
            return "ml"
        return None
