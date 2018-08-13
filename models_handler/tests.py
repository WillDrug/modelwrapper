import os
import shelve
from datetime import datetime
from unittest import TestCase
from models_handler.core import ModelInterface, ModelLoader, Config
from models_handler import fit, predict, current_loader
from numpy.core.multiarray import ndarray
from sklearn.exceptions import NotFittedError
from sklearn.svm import SVC

DUMPS_PATH = os.environ['DUMPS_PATH']
MODEL_NAME = 'TestModel1'


class TestModelLoader(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loader = ModelLoader(MODEL_NAME)

    @classmethod
    def tearDownClass(cls):
        join = os.path.join(DUMPS_PATH, MODEL_NAME)
        if os.path.exists(join) and os.path.isfile(join):
            os.remove(join)

    def test_loader_instance(self):
        self.assertIsInstance(self.loader, ModelLoader)

    def test_model_list(self):
        model_list = getattr(self.loader, "_ModelLoader__model_list")
        keys = {'TestModel1', 'TestModel2', 'BTtC_Model'}
        self.assertTrue(type(model_list) == dict)
        self.assertSetEqual(set(model_list.keys()), keys)

    def test_model_subclasses(self):
        for k, model in getattr(self.loader, "_ModelLoader__model_list").items():
            self.assertTrue(issubclass(model, ModelInterface))

    def test_init(self):
        self.assertTrue(issubclass(self.loader.model, ModelInterface))


class TestModelInterface(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = ModelLoader(MODEL_NAME).model()

    def setUp(self):
        self.model.load_model_core(Config.LATEST_TAG)

    def tearDown(self):
        join = os.path.join(DUMPS_PATH, MODEL_NAME)
        if os.path.exists(join) and os.path.isfile(join):
            os.remove(join)

    def test_init(self):
        self.assertTrue(issubclass(self.model.__class__, ModelInterface))

    def test_methods(self):
        mthd = [
            'fit',
            'predict',
            'score',
            '_update_meta',
            'dump_model_core',
            'load_model_core',
            'delete_model_core',
        ]
        for m in mthd:
            self.assertIn(m, dir(self.model))

    def test_variables(self):
        vars = [
            'model_path',
            'model_core',
            'model_versions',
            'model_name',
            'model_config',
            'metadata'
        ]
        for v in vars:
            self.assertIn(v, dir(self.model))

    def test_load_model_core(self):
        dump_path = os.path.join(DUMPS_PATH, MODEL_NAME)

        # initialises with default SVC core
        self.model.load_model_core(Config.LATEST_TAG)
        self.assertIsInstance(self.model.model_core, SVC)

        # save & reload core
        self.model.dump_model_core(Config.LATEST_TAG)
        self.model.load_model_core(Config.LATEST_TAG)
        self.assertIsInstance(self.model.model_core, SVC)

        # verify shelve state
        db = shelve.open(dump_path)
        self.assertListEqual(sorted([Config.LATEST_TAG]), sorted(list(db.keys())))
        self.assertEqual(1, len(db.keys()))
        print('Shelve keys:', list(db.keys()))
        db.close()

    def test_dump_model_core(self):
        # save core as latest
        dump_path = os.path.join(DUMPS_PATH, MODEL_NAME)
        self.model.dump_model_core()
        db = shelve.open(dump_path)
        self.assertListEqual(sorted([Config.LATEST_TAG]), sorted(list(db.keys())))
        self.assertEqual(1, len(db.keys()))
        db.close()

        # save core with custom name. Should be [latest,test] in shelve
        self.model.dump_model_core(dump_id='test')
        db = shelve.open(dump_path)
        self.assertListEqual(sorted([Config.LATEST_TAG, 'test']), sorted(list(db.keys())))
        self.assertEqual(2, len(db.keys()))
        db.close()

        # save core with champion flag. Old latest model will be resaved with timestamp as it's tag
        # should be [latest, test, YYYY-MM-DDThh:mm:ss.ssss] in shelve.
        self.model.dump_model_core(new_champ=True)
        db = shelve.open(dump_path)
        self.assertEqual(3, len(db.keys()))
        print('Shelve keys:', list(db.keys()))
        db.close()

    def test_delete_model_core(self):
        dump_path = os.path.join(DUMPS_PATH, MODEL_NAME)

        # saves model as latest
        self.model.dump_model_core()
        db = shelve.open(dump_path)
        self.assertListEqual(sorted([Config.LATEST_TAG]), sorted(list(db.keys())))
        self.assertEqual(1, len(db.keys()))
        db.close()

        # saves model as test. Should be [latest,test] in shelve
        self.model.dump_model_core(dump_id='test')
        db = shelve.open(dump_path)
        self.assertListEqual(sorted([Config.LATEST_TAG, 'test']), sorted(list(db.keys())))
        self.assertEqual(2, len(db.keys()))
        db.close()

        # delete test fro, shelve. Only [latest] should remain in shelve
        self.model.delete_model_core('test')
        db = shelve.open(dump_path)
        self.assertListEqual(sorted([Config.LATEST_TAG]), sorted(list(db.keys())))
        self.assertEqual(1, len(db.keys()))
        print('Shelve keys:', list(db.keys()))
        db.close()

    def test_update_meta(self):
        dt_want = datetime.now()
        self.model._update_meta()

        self.assertIn(Config.LAST_LAUNCH_DATE, self.model.metadata)
        self.assertIn(Config.LAST_LAUNCH_TIME, self.model.metadata)

        # test skip microseconds as they may differ a lot, depending on runtime
        self.assertEqual(dt_want.date(), self.model.metadata[Config.LAST_LAUNCH_DATE])
        self.assertEqual(dt_want.time().hour, self.model.metadata[Config.LAST_LAUNCH_TIME].hour)
        self.assertEqual(dt_want.time().minute, self.model.metadata[Config.LAST_LAUNCH_TIME].minute)
        self.assertEqual(dt_want.time().second, self.model.metadata[Config.LAST_LAUNCH_TIME].second)

    def test_fit(self):
        res = self.model.fit()
        self.assertTrue(type(res) == bool)

    def test_predict(self):
        # override setUp() and clear dump
        if os.path.exists(os.path.join(DUMPS_PATH, MODEL_NAME)):
            self.tearDown()

        # model should not work if it's core not loaded
        with self.assertRaises(NotFittedError):
            self.model.predict()

        self.model.load_model_core(Config.LATEST_TAG)
        self.assertIsInstance(self.model.model_core, SVC)

        # model still should not work if it's core not fitted
        with self.assertRaises(NotFittedError):
            self.model.predict()

        fit_res = self.model.fit()
        self.assertIsInstance(fit_res, bool)

        # prediction should be ready
        predict_res = self.model.predict()

        self.assertIsInstance(predict_res, bool)

        # check that prediction exists
        self.assertTrue(type(self.model.prediction) is not None)
        self.assertIsInstance(self.model.prediction, ndarray)

        # try to save and load a model into another instance
        # after that run predict - should be ready without additional fit
        self.model.dump_model_core('test')
        model2 = ModelLoader(MODEL_NAME).model()
        model2.load_model_core('test')

        # check that model version list is correct during loading from shelve
        db = shelve.open(os.path.join(DUMPS_PATH, MODEL_NAME))
        self.assertEqual(list(db.keys()), model2.model_versions)

        # check that models core are of the same class
        self.assertEqual(self.model.model_core.__class__, model2.model_core.__class__)
        # but different instances
        self.assertNotEqual(self.model, model2)
        # though their inner settings should be equal
        self.assertEqual(self.model.model_core.__repr__(), model2.model_core.__repr__())

        predict_res2 = model2.predict()
        self.assertIsInstance(predict_res2, bool)

        # check that prediction exists
        self.assertTrue(type(model2.prediction) is not None)
        self.assertIsInstance(model2.prediction, ndarray)

    def test_score(self):
        sc = self.model.score()
        self.assertIsInstance(sc, float)
        self.assertTrue(0 <= sc <= 1)


class TestApiMethods(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = ModelLoader(MODEL_NAME).model()

    def tearDown(self):
        join = os.path.join(DUMPS_PATH, MODEL_NAME)
        if os.path.exists(join) and os.path.isfile(join):
            os.remove(join)

    def test_fit_with_dump(self):
        # initialize dump
        self.model.load_model_core(Config.LATEST_TAG)
        self.model.dump_model_core(Config.LATEST_TAG)

        dumps_path = os.path.join(DUMPS_PATH, MODEL_NAME)
        self.assertTrue(all([os.path.exists(dumps_path), os.path.isfile(dumps_path)]))

        db = shelve.open(dumps_path)
        self.assertEqual(1, len(list(db)))
        old_model = db[Config.LATEST_TAG]
        db.close()
        self.assertEqual(old_model['model'].__class__, self.model.model_core.__class__)
        self.assertIsInstance(self.model.model_core, SVC)

        status, res = fit(self.model)
        self.assertIsInstance(status, bool)

        # retry and clear db until get state where old champion wins (status will be false)
        while status:
            db = shelve.open(dumps_path)
            db_keys = list(db)
            for k in filter(lambda x: x != Config.LATEST_TAG, db_keys):
                db[Config.LATEST_TAG] = db[k]
                del db[k]
            db.close()
            status, res = fit(self.model)

        db = shelve.open(dumps_path)
        db_keys = list(db)
        print("Checking old champion")
        print("All db keys:", db_keys)
        new_model = db[Config.LATEST_TAG]
        self.assertEqual(1, len(db_keys), "Keys after cleanup - champion case")
        self.assertEqual(old_model.__repr__(), new_model.__repr__())

        # clean everything except latest
        for k in filter(lambda x: x != Config.LATEST_TAG, db_keys):
            del db[k]
        old_model = db[Config.LATEST_TAG]
        self.assertEqual(1, len(list(db.keys())))
        self.assertEqual(Config.LATEST_TAG, list(db_keys)[0])
        self.assertEqual(old_model.__repr__(), db[Config.LATEST_TAG].__repr__())
        db.close()

        # retry and clear db until get state where challenger wins (status will be true)
        while not status:
            status, res = fit(self.model)
            db = shelve.open(dumps_path)
            db.close()

        db = shelve.open(dumps_path)
        db_keys = list(db.keys())
        print("Checking new champion")
        self.assertEqual(2, len(db_keys), "Keys after challenger win")
        new_model = db[Config.LATEST_TAG]

        # New model shouldn't match
        self.assertNotEqual(old_model.__repr__(), new_model.__repr__())
        print("All db keys:", db_keys)
        db_keys.remove(Config.LATEST_TAG)
        self.assertEqual(1, len(db_keys), "Keys after removing latest model")
        print("Old model key:", db_keys)
        archived_model = db[db_keys[0]]
        self.assertEqual(old_model.__repr__(), archived_model.__repr__())
        db.close()

    def test_predict(self):
        # initialize dump
        self.model.load_model_core(Config.LATEST_TAG)
        self.model.dump_model_core(Config.LATEST_TAG)
        dumps_path = os.path.join(DUMPS_PATH, MODEL_NAME)
        self.assertTrue(all([os.path.exists(dumps_path), os.path.isfile(dumps_path)]))

        res = predict(self.model)
        print('Prediction status:', res)
        self.assertIsInstance(res, bool)
        self.assertEqual(True, res)
        pred = self.model.prediction
        print('Prediction result:', pred)
        self.assertIsInstance(pred, ndarray)

    def test_fit_with_no_dump(self):
        new_model = ModelLoader(MODEL_NAME).model()
        status, res = fit(new_model)
        self.assertIsInstance(status, bool)
        self.assertIsInstance(res, bool)

    def test_predict_with_no_dump(self):
        new_model = ModelLoader(MODEL_NAME).model()
        res = predict(new_model)
        print('Prediction status:', res)
        self.assertIsInstance(res, bool)
        self.assertEqual(True, res)
        pred = new_model.prediction
        print('Prediction result:', pred)
        self.assertIsInstance(pred, ndarray)
