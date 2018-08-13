from copy import copy
from sklearn.exceptions import NotFittedError
from models_handler.core import ModelLoader, Config, ModelInterface
from uuid import uuid4
from orchestrator import l

current_loader = ModelLoader


def fit(model: ModelInterface):  # TODO: some better version control =\
    try:
        model.load_model_core(Config.LATEST_TAG)  # here NotFitted would be raised
        champ_score = model.score()

        challenger = copy(model)

        fit_result = challenger.fit()
        challenger_score = challenger.score()
        if challenger_score > champ_score:
            status = True
            l.info(f'LADIES AND GENTLEMEN, YOUR NEW MACHINE LEARNING CHAMPION!!! ({champ_score}<{challenger_score})')
            challenger.dump_model_core(new_champ=True)  # new champion always would be LATEST
        else:
            status = False
            l.info(f'LADIES AND GENTLEMEN, STILL YOUR MACHINE LEARNING CHAMPION!!! ({champ_score}>{challenger_score})')
            challenger.dump_model_core(new_champ=False)
    except NotFittedError as e:
        status = True
        fit_result = model.fit()
        model.dump_model_core(dump_id='initial', new_champ=True)

    return status, fit_result


def predict(model: ModelInterface):
    l.info(f'Trying to predict {model.__class__}')
    try:
        model.load_model_core(Config.LATEST_TAG)
    except NotFittedError as e:
        l.warning(f'Predict called on not fitted model!')
        model.fit()
        model.dump_model_core(dump_id='initial', new_champ=True)
    rs = model.predict(write_out=True)
    return rs


def delete_model_dump(model: ModelInterface, **kwargs):
    if 'dump_id' not in kwargs:
        raise KeyError('Dump id for deletion is not specified')
    return model.delete_model_core(dump_id=str(kwargs['dump_id']))


def show_dumps_list(model: ModelInterface, **kwargs):
    return model.show_dumps()


def restore_model_dump(model: ModelInterface, **kwargs):
    if 'dump_id' not in kwargs:
        raise KeyError('Dump id for restoration is not specified')
    return model.restore_dump(dump_id=str(kwargs['dump_id']))
