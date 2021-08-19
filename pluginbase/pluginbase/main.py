from .pluginbase import TextProcessor


def test():
    processor = TextProcessor()
    print(processor.PLUGINS)
    processed = processor.process(text="**foo bar**", plugins=('plugin1', ))
    print(processed)
    processed = processor.process(text="--foo bar--")
    print(processed)
