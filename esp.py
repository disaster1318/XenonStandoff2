from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Rectangle
from kivy.core.window import Window

class ESPOverlay(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size = Window.size
        self.pos = (0, 0)
        self.players = []

    def update_players(self, players):
        self.players = players
        self.draw()

    def draw(self):
        self.canvas.clear()
        if not self.players:
            return

        for player in self.players:
            x, y, z = player["pos"]
            health = player["health"]
            team = player["team"]

            screen_x = x / 10 + self.width / 2
            screen_y = -y / 10 + self.height / 2

            with self.canvas:
                Color(1, 0, 0, 1) if team == 1 else Color(0, 0, 1, 1)
                Line(rectangle=(screen_x - 25, screen_y - 50, 50, 100), width=2)

                Color(0, 1, 0, 1)
                Line(rectangle=(screen_x - 30, screen_y - 50, 5, health / 100 * 100), width=2)

                Color(1, 1, 0, 0.5)
                Line(points=[self.width/2, 0, screen_x, screen_y], width=1)

    def clear(self):
        self.canvas.clear()
