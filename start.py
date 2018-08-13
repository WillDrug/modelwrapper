from orchestrator import Api, Tasker, Conductor, l
from models_handler import current_loader, predict, fit, show_dumps_list, delete_model_dump, restore_model_dump
from time import sleep
# DON'T USE DOTS HERE
Conductor.ORCHESTRATION = 'model_wrapper:2'



def test_task(sleep_time:int=0, response:str='OK', fail:bool=False, **kwargs):
    sleep(sleep_time)
    if fail:
        raise ArithmeticError('Oh no you dodn\'t!')
    else:
        return response


def fit_task(model_name: str, **kwargs) -> dict:
    model = current_loader(model_name).model()
    status, ft = fit(model)
    return ft

def predict_task(model_name: str, **kwargs) -> dict:
    model = current_loader(model_name).model()
    pr = predict(model)
    return pr

def model_dump_control(model_name: str='', restore: bool=False, dump_id: str='') -> str:
    model = current_loader(model_name).model()
    if restore:
        return restore_model_dump(model, dump_id=dump_id)
    else:
        return delete_model_dump(model, dump_id=dump_id)

def model_dump_show(model_name: str=''):
    model = current_loader(model_name).model()
    return show_dumps_list(model)

t = Tasker()

t.register_task('fit', fit_task)
t.register_task('predict', predict_task)
t.register_task('test', test_task)

t.register_task('dumpdump', model_dump_show)
t.register_task('controldump', model_dump_control)

a = Api(tasker=t)
a.start()


