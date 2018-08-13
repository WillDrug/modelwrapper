import base64
import hashlib
from enum import Enum
import importlib
import json
import os
import pkgutil
import shelve
from abc import ABCMeta, abstractmethod
from datetime import datetime
from sklearn.exceptions import NotFittedError

class Config(Enum):
    LATEST_TAG = 'latest'
    MODELS_FOLDER = 'models'
    MODEL_CFG_FILE = 'config.json'
    MODEL_CFG = 'model'
    MODEL_CONN_CFG = 'connections'
    LAST_LAUNCH_DATE = 'last_launch_date'
    LAST_LAUNCH_TIME = 'last_launch_time'
    DUMP_MODEL_SECTION = 'model'
    DEMP_META_SECTION = 'description'

    def __get__(self, instance, owner):
        return self.value


DUMPS_PATH = os.environ['DUMPS_PATH']


class ModelInterface(metaclass=ABCMeta):
    """
    Generic interface for creating model launcher, that can be found and loaded dynamically by ModelLoader.
    Every model MUST have a launcher class, subclassing this interface.
    Models can have multiple implementations of this interface, though it makes no sense in general
    """

    def __init__(self, file=__file__):
        """
        Existing model loads by id. New models get timestamp as id.

        1) MUST BE OVERRIDED IN EVERY MODEL
        2) MUST ME OVERRIDED STRICTLY & ONLY THIS WAY:
            def __init__(self):
                super().__init__(__file__)
        """
        self.__dump_path = os.path.join(DUMPS_PATH, self.__class__.__name__)  # path to model dump in dumps folder
        self.model_path = os.path.dirname(file)  # path to model folder

        self.model_core = None  # model itself
        try:
            with shelve.open(self.__dump_path) as db:  # list of all model versions
                self.model_versions = list(db.keys())
                db.close()
        except OSError:
            self.model_versions = []

        with open(os.path.join(os.path.dirname(file), Config.MODEL_CFG_FILE), 'r', encoding='utf-8') as fl:
            cfg = json.load(fl)
        fl.close()

        self.model_name = self.__class__.__name__
        self.score_ball = 0
        self.model_config, self.conn_config = cfg[Config.MODEL_CFG], cfg[
            Config.MODEL_CONN_CFG]  # configs for model core and connections

        # metadata
        self.metadata = {}

    def _update_meta(self):
        dt = datetime.now()
        self.metadata[Config.LAST_LAUNCH_DATE] = dt.date()
        self.metadata[Config.LAST_LAUNCH_TIME] = dt.time()

    @abstractmethod
    def fit(self):
        """
        Used to launch model fitting.
        Implementation is totally yours, but in terms of compatibility
        return True if fitting is successful or False if failed.
        """
        pass

    @abstractmethod
    def predict(self):
        """
        Used to launch prediction.
        Implementation is totally yours, but in terms of compatibility
        save prediction result to self.prediction and then return self.prediction.
        """
        pass

    @abstractmethod
    def score(self):
        """
        Used to get model score for champion / challenger comparision.
        Implementation is totally yours, but in terms of compatibility
        save scoring result as aggregated ball to self.score_res and then return self.score_res.
        """
        pass

    @abstractmethod
    def dump_model_core(self, dump_id: str = str(datetime.now()), new_champ: bool = False):
        """
        Saves model core to binary object.
        It's up to you - either to use default implementation or make your own.
        """
        if not os.path.exists(DUMPS_PATH):
            os.mkdir(DUMPS_PATH, mode=0o777)  # checks and creates dumps folder inside modelwrapper root

        db = shelve.open(self.__dump_path)

        self._update_meta()
        db[dump_id] = {
                'saved': datetime.now(),
                'description': self.metadata,
                'model': self.model_core,
                'score': self.score()
            }
        if new_champ:  # latest updates only on new champ. latest always loads by default
            db[Config.LATEST_TAG] = db.get(dump_id)

        db.close()
        return True

    @abstractmethod
    def load_model_core(self, dump_id: str):
        """
        Loads model core from specific binary object.
        It's up to you - either to use default implementation or make your own.
        """
        if not os.path.exists(DUMPS_PATH):
            os.mkdir(DUMPS_PATH, mode=0o777)  # checks and creates dumps folder inside modelwrapper root
        db = shelve.open(self.__dump_path)
        model = db.get(dump_id)
        db.close()
        if model is None:
            raise NotFittedError()
        self.model_core = model[Config.DUMP_MODEL_SECTION]
        self.metadata = model[Config.DEMP_META_SECTION]
        self.score_ball = model['score']
        return True

    @abstractmethod
    def delete_model_core(self, dump_id: str):
        """
        Deletes specified model version from dump
        """
        db = shelve.open(self.__dump_path)
        del db[dump_id]
        db.close()
        return True

    def show_dumps(self):
        try:
            db = shelve.open(self.__dump_path)
            return {x: {
                'saved': str(db[x]['saved']),
                'description': str(db[x]['description']),
                'model': str(db[x]['model'].__class__.__name__),
                'score': self.score()
            } for x in db}
        finally:
            db.close()

    def restore_dump(self, dump_id: str):
        self.load_model_core(dump_id=dump_id)
        self.dump_model_core(dump_id=dump_id, new_champ=True)
        return True


class ModelLoader:
    """
    Loads models from folders dynamically.
    """

    def __init__(self, model_name: str):
        self.__model_list = None
        self.__base_folder = os.path.join(os.path.dirname(__file__), Config.MODELS_FOLDER)
        self._import_models()  # load models recursively based on ModelInterface implementation
        self.model = self.__model_list[model_name]

    def _import_models(self) -> None:
        """
        Finds all ModelInterface subclasses and treats them as models. Imports them dynamically.
        """
        for model in os.listdir(self.__base_folder):  # check models dir and it's subfolders. os.walk is not convenient
            pkg_dir = os.path.join(self.__base_folder, model)
            for (finder, name, ispkg) in pkgutil.iter_modules([pkg_dir]):
                # dynamically import packages from models/{model_name}/ folder
                importlib.import_module(f'{__package__}.models.{model}.{name}')

        # generates a dict of ModelInterface implementations
        self.__model_list = {subcl.__name__: subcl for subcl in ModelInterface.__subclasses__()}
