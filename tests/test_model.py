from concurrent.futures import ThreadPoolExecutor
import threading
import time

from src.cropshield import model as model_module


def test_keras_model_loading_is_serialized(monkeypatch, tmp_path):
    model_path = tmp_path / "model.keras"
    model_path.touch()
    counter_lock = threading.Lock()
    active_loads = 0
    max_active_loads = 0
    sentinel = object()

    def fake_load_model(_path):
        nonlocal active_loads, max_active_loads
        with counter_lock:
            active_loads += 1
            max_active_loads = max(max_active_loads, active_loads)
        time.sleep(0.02)
        with counter_lock:
            active_loads -= 1
        return sentinel

    monkeypatch.setattr(model_module.tf.keras.models, "load_model", fake_load_model)

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(model_module.load_model, [model_path] * 4))

    assert results == [sentinel] * 4
    assert max_active_loads == 1
