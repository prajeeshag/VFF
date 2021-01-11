
from sorl.thumbnail.engines.pil_engine import Engine as CoreEngine


class Engine(CoreEngine):

    def create(self, image, geometry, options):
        image = self.orientation(image, geometry, options)
        return super().create(image, geometry, options)
