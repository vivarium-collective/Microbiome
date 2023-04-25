from vivarium.core.process import Process
from vivarium.core.engine import Engine, pf
import numpy as np
from cobra.io import read_sbml_model
from cobra.util import create_stoichiometric_matrix

class DynamicFBA(Process):
    defaults = {}

    def __init__(self, parameters=None):
        super().__init__(parameters=parameters)
        self.model = read_sbml_model(self.parameters["model_file"])
        self.bounds = self.extract_bounds()

    def extract_bounds(self):
        bounds = {}
        for reaction in self.model.reactions:
            bounds[reaction.id] = (reaction.lower_bound, reaction.upper_bound)
        return bounds

    def reaction_bound_change(self, percentage):  #This is an aging process which in each timestep we reduce 10% of flux bounds
        for reaction in self.model.reactions:
            old_bounds = self.bounds[reaction.id]
            new_bounds = (old_bounds[0] * (1 - percentage), old_bounds[1] * (1 - percentage))
            reaction.lower_bound, reaction.upper_bound = new_bounds
            self.bounds[reaction.id] = new_bounds

    def ports_schema(self):
        return {
            "fluxes": {
                '_default': {},
                '_emit': True,
                "_updater": "set"
            },
            "reactions": {
                '_default': [str(reaction) for reaction in self.model.reactions],
                '_emit': True,
                "_updater": "set"
            },
            "objective_flux": {
                '_default': 0.0,
                '_emit': True,
                "_updater": "set"
            },
            "reaction_bounds": {
                '_default': self.bounds,
                '_emit': True,
                "_updater": "set"
            }
        }

    def next_update(self, timestep, state):
        # Use provided reaction_bounds for optimizing the model
        reaction_bounds = state["reaction_bounds"]
        for reaction_id, (lower_bound, upper_bound) in reaction_bounds.items():
            reaction = self.model.reactions.get_by_id(reaction_id)
            reaction.lower_bound, reaction.upper_bound = lower_bound, upper_bound

        self.reaction_bound_change(0.1)  # Apply 10% reaction_bound_change
        solution = self.model.optimize()
        objective_value = solution.objective_value
        fluxes = solution.fluxes.to_dict()
        return {
            "fluxes": fluxes,
            "objective_flux": objective_value,
            "reaction_bounds": self.bounds
        }


def main(model_path, simulation_time):
    parameters = {"model_file": model_path}
    dynamic_fba = DynamicFBA(parameters)
    processes = {'DynamicFBA': dynamic_fba}
    topology = {
        'DynamicFBA': {
            'fluxes': ("fluxes_values",),
            'reactions': ("reactions_list",),
            'objective_flux': ("objective_flux_value",),
            'reaction_bounds': ("reaction_bounds",),  # Connect the reaction_bounds output to the input
        }
    }
    sim = Engine(processes=processes, topology=topology)
    sim.update(simulation_time)
    data = sim.emitter.get_data()
    output = pf(data)
    return output, processes, topology
