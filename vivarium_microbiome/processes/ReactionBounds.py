from vivarium.core.process import Process
from cobra.io import read_sbml_model

class ReactionBounds(Process):
    """
    This class initializes and updates the reaction bounds for the model.

    ReactionBounds ingests a COBRA model, creating an initial dictionary of reaction bounds. For each update, it adjusts the reaction bounds considering a predefined aging percentage and resource limitation. The resource limitation is evaluated based on the available resources and their consumption at each timestep. This class now also computes the current_v0 value, which represents the flux calculated using the current glucose concentration by the Michaelis-Menten equation.
    """

    defaults = {
        'model_file': None,
        'enz_concentration': 5,
        'kcat': 5,
        'init_concentration': 11.1,
    }

    def __init__(self, parameters=None):
        super().__init__(parameters=parameters)
        self.model = read_sbml_model(self.parameters['model_file'])
        self.bounds = self.initialize_bounds()
        self.initial_upper_bound = None # an attribute to hold the initial upper bound
        self.initial_lower_bound = None

    def initialize_bounds(self):
        bounds = {}
        for reaction in self.model.reactions:
            bounds[reaction.id] = (reaction.lower_bound, reaction.upper_bound)
        return bounds

    def ports_schema(self):
        return {
            "reaction_bounds": {
                '_default': self.bounds,
                '_emit': True,
                '_updater': 'set'
            },
            "current_v0": {
                '_default': -10.0,
                '_emit': True,
                '_updater': 'set'
            },
            "concentration": {
                '_default': self.parameters['init_concentration'],
                '_emit': True,
                "_updater": "accumulate",
            },
            "enz_concentration": {
                "_default": self.parameters['enz_concentration'],
                "_updater": "set"
            },
        }

    def next_update(self, timestep, state):
        concentration = state['concentration']
        enz_concentration = state['enz_concentration']  # Use 'enz_concentration' instead of 'enz-conc'
        vmax = self.parameters['kcat'] * enz_concentration
        current_v0 = vmax * concentration / (self.parameters['km'] + concentration)
        current_v0 = - current_v0  # it should be negative because it consumes glucose
        updated_bounds = self.bounds
        if timestep != 0:
            current_bounds = state["reaction_bounds"]
            for reaction_id, old_bounds in current_bounds.items():
                if reaction_id == "EX_glc__D_e":  # it will be always none if the class was Step instead of Process. why?
                    if self.initial_lower_bound is None:  # If the initial lower bound has not been stored yet
                        self.initial_lower_bound = old_bounds[0]  # Store the initial lower bound
                    new_lower_bound = max(self.initial_lower_bound, current_v0)  # Take the maximum of the initial lower bound and current_v0
                    new_bounds = (new_lower_bound, old_bounds[1])  # keep the old upper bound
                    updated_bounds[reaction_id] = new_bounds

        return {
            "reaction_bounds": updated_bounds,
            "current_v0": current_v0,
        }

