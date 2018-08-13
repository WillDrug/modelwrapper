from models_handler.core import ModelInterface, Config


class TestModel2(ModelInterface):

    def __init__(self):
        super().__init__(__file__)

    def fit(self) -> dict:
        return {
            "success": True,  # TODO: FIX
            "some_data": "terfe=d=fb-b-fwer-tw"
        }

    def predict(self) -> dict:
        return {
            "success": True,  # TODO: FIX
            "some_data": "terfe=d=fb-b-fwer-tw"
        }

    def score(self) -> int:
        return 1

    def dump_model_core(self, dump_id: str = Config.LATEST_TAG, new_champ: bool = False):
        pass

    def load_model_core(self, dump_id: str):
        pass

    def delete_model_core(self, dump_id: str):
        pass
