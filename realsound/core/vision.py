from realsound.cv import harris
import numpy as np


class VisionLayer:
    def __init__(self):
        pass

    def see(self, frame, settings):
        # Get object corners using harris algorithm
        corners = harris.get_corners(frame, settings)

        # Identify object shapes using corners
        shapes = harris.detect(np.reshape(corners, (-1, 2)), frame.shape)

        # Classify Entities (i.e. ball & paddles) from shapes
        return harris.classify(shapes)
