from vivarium.core.process import Step
import random

# Add the Time_proportion variable, We consider each time-step a minute
TIME_PROPORTION = (1 / 60)  # we set each time-step as an hour and the Time_proportion as a minute

class RegulatoryProtein(Step):
    """
    This class generates a random number (regulation_probability) between 0.0001 and 1.
    """
    defaults = {
        'regulation_probability': 0.5,
    }

    def ports_schema(self):
        return {
            'regulation_probability': {
                '_default': self.parameters['regulation_probability'],
                '_emit': True,
                "_updater": "set"
            },
        }

    def next_update(self, timestep, state):
        regulation_probability = random.uniform(0.0001, 1)
        return {
            'regulation_probability': regulation_probability
        }

