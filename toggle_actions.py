class ToggleActions:
    def __init__(self, window, registry_tweaks):
        self.window = window
        self.registry = registry_tweaks

    def toggle_game_bar(self, state):
        return self.registry.disable_game_bar(self.window, state)

    def toggle_fullscreen_optimizations(self, state):
        return self.registry.disable_fullscreen_optimizations(self.window, state)

    def toggle_power_plan(self, state):
        return self.registry.set_high_performance_power_plan(self.window, state)

    def toggle_animations(self, state):
        return self.registry.disable_animations(self.window, state)

    def toggle_ntfs(self, state):
        return self.registry.optimize_ntfs(self.window, state)