config = None
_pipeline = None


def get_config():
    global config
    if config is None:
        from config import AppConfig
        config = AppConfig()
    return config


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        from config import AppConfig
        from src.pipeline import RAGPipeline
        config = get_config()
        _pipeline = RAGPipeline(config)
    return _pipeline


def update_pipeline_config(new_config_data: dict):
    global _pipeline, config
    config = get_config()
    config.update_from_dict(new_config_data)
    if _pipeline is not None:
        _pipeline.update_config(config)
    return config
