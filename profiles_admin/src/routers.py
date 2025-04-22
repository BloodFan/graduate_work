class UnifiedRouter:
    route_app_labels = {"profiles", "favorites", "reviews"}

    def db_for_read(self, model, **hints):
        if model._meta.model_name in ["profile", "favorite", "review"]:
            return "profiles_db"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.model_name in ["profile", "favorite", "review"]:
            return "profiles_db"
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            return db == "profiles_db"
        return db == "default"
