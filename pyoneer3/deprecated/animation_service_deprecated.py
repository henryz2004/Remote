class AnimationService:

    def __init__(self):

        self.animations = []

    def update(self, delta):

        self.animations = [animation for animation in self.animations if animation.alive]
        for animation in self.animations:
            animation.update(delta)
