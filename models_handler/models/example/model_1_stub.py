import os

import pandas as pd
from sklearn import datasets, svm, model_selection

from models_handler.core import ModelInterface


class TestModel1(ModelInterface):

    def __init__(self):
        super().__init__(__file__)

    def fit(self) -> bool:
        try:
            self._load_data()
            self.model_core.fit(X=self.train_x, y=self.train_y)
            res = True
        except Exception as e:
            res = False
            raise e
        return res

    def predict(self) -> bool:
        self._load_data()
        self.prediction = self.model_core.predict(X=self.test_x)
        return True if len(self.prediction) > 0 else False

    def score(self) -> float:
        try:
            self.score_res = 1 - sum([0 if x[0] == x[1] else 1 for x in zip(self.prediction, self.test_y)]) / len(
                self.prediction)
        except Exception as e:
            print(e)
            return 0.99
        return self.score_res

    def _load_data(self):
        iris_set = datasets.load_iris()
        data = pd.DataFrame(iris_set['data'], columns=iris_set['feature_names'])
        target = pd.Series(iris_set['target'], name='target')
        self.train_x, self.test_x, self.train_y, self.test_y = model_selection.train_test_split(data, target,
                                                                                                train_size=0.6)

    def dump_model_core(self, dump_id: str = 'latest', new_champ: bool = False):
        super().dump_model_core(dump_id=dump_id, new_champ=new_champ)

    def load_model_core(self, dump_id: str):
        try:
            super().load_model_core(dump_id=dump_id)
        except Exception:
            self.model_core = svm.SVC()

    def delete_model_core(self, dump_id: str):
        super().delete_model_core(dump_id)
