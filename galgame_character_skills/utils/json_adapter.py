from flask import jsonify, request


class JsonApiAdapter:
    @staticmethod
    def body():
        return request.get_json(silent=True) or {}

    @staticmethod
    def response(result):
        return jsonify(result)

    def run(self, handler, *args, **kwargs):
        return self.response(handler(*args, **kwargs))

    def run_with_body(self, handler, *args, **kwargs):
        return self.run(handler, self.body(), *args, **kwargs)


__all__ = ["JsonApiAdapter"]
