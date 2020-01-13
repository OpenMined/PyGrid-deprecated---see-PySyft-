from .scope import Scope


class ScopeController:
    def __init__(self):
        self.scopes = {}

    def create_scope(self, worker_id, protocol):
        scope = Scope(worker_id, protocol)
        self.scopes[scope.id] = scope
        return self.scopes[scope.id]

    def delete_scope(self, scope_id):
        del self.scopes[scope_id]

    def get_scope(self, scope_id):
        return self.scopes.get(scope_id, None)
