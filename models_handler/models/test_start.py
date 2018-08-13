import argparse

from orchestrator import Api, Tasker, Conductor, l
from models_handler import current_loader, predict, fit
from time import sleep

# DON'T USE DOTS HERE
Conductor.ORCHESTRATION = 'model_wrapper:2'


def test_task(sleep_time: int = 0, response: str = 'OK', fail: bool = False, **kwargs):
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate report from parsed dialogs json files, save to .csv")
    parser.add_argument('-m', dest='mode', type=str, help='Fit or predict mode', required=True)
    parser.add_argument('-n', dest='model', type=str, help='Model name', required=True)
    args = parser.parse_args()
    func = {
        'fit': fit_task,
        'predict': predict_task,
    }[args.mode]
    func(args.model)
