import core.mosdac_worker as worker


def test_worker_stays_disabled_without_credentials(monkeypatch):
    monkeypatch.setattr(worker, "mosdac_is_configured", lambda: False)
    assert worker.run_once()["status"] == "DISABLED"


def test_mdapi_config_uses_noninteractive_download(monkeypatch):
    monkeypatch.setattr(worker.Config, "MOSDAC_USERNAME", "user")
    monkeypatch.setattr(worker.Config, "MOSDAC_PASSWORD", "password")
    monkeypatch.setattr(worker.Config, "MOSDAC_DATASET_ID", "dataset")
    config = worker.build_mdapi_config("/data")
    assert config["download_settings"]["skip_user_prompt"] is True
    assert config["search_parameters"]["datasetId"] == "dataset"
