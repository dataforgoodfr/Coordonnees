from coordo.sources.kobotoolbox import KoboToolboxSource


def parse_source(config):
    type_ = config.pop("type")
    parsers = {
        "kobotoolbox": KoboToolboxSource,
    }
    return parsers[type_](**config)
