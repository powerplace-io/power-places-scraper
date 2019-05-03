import os
from jinja2 import Environment, FileSystemLoader, select_autoescape

from places_scraper.data_util import ensure_dirs_exist


class BaseReport:
    template_base = os.path.join(os.path.dirname(__file__), "templates")

    def __init__(self, output_base):
        self.env = Environment(
            loader=FileSystemLoader(searchpath=self.template_base),
            autoescape=select_autoescape(['html', 'xml'])
        )
        self.output_base = output_base

    def apply_template(self, target, kwargs, template=None):
        fn = "{}.html".format(target)
        t = self.env.get_template(template or fn)
        path = os.path.join(self.output_base, fn)
        ensure_dirs_exist(path)
        with open(path, 'w') as f:
            f.write(
                t.render(**kwargs)
            )
        return fn

    def build(self, *args, **kwargs):
        raise NotImplementedError
