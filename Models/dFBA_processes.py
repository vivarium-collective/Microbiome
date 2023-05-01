from vivarium.core.process import Process
from vivarium.core.engine import Engine, pf
import numpy as np
from cobra.io import read_sbml_model
from cobra.util import create_stoichiometric_matrix

class ReactionBounds(Process):
    defaults = {}

    def __init__(self, parameters=None):
        super().__init__(parameters=parameters)
        self.model = read_sbml_model(self.parameters["model_file"])
        self.bounds = self.initialize_bounds()

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
                "_updater": "set"
            }
        }

    def next_update(self, timestep, state):
        # Apply 10% reaction_bound_change, it can be any function the user wants
        percentage = 0.1
        updated_bounds = {}

        if timestep == 0:
            updated_bounds = self.bounds
        else:
            current_bounds = state["reaction_bounds"]  # Use the current state's bounds
            for reaction_id, old_bounds in current_bounds.items():
                new_bounds = (
                old_bounds[0] * (1 - (percentage * timestep)), old_bounds[1] * (1 - (percentage * timestep)))
                updated_bounds[reaction_id] = new_bounds

        return {"reaction_bounds": updated_bounds}


class DynamicFBA(Process):
    defaults = {}

    def __init__(self, parameters=None, reaction_bounds=None):
        super().__init__(parameters=parameters)
        self.model = read_sbml_model(self.parameters["model_file"])
        self.reaction_bounds = reaction_bounds

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
                '_default': self.reaction_bounds.bounds if self.reaction_bounds else {},
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

        solution = self.model.optimize()
        objective_value = solution.objective_value
        fluxes = solution.fluxes.to_dict()
        return {
            "fluxes": fluxes,
            "objective_flux": objective_value
        }

def main(model_path, simulation_time):
    parameters = {"model_file": model_path}
    reaction_bounds = ReactionBounds(parameters)
    dynamic_fba = DynamicFBA(parameters, reaction_bounds)
    processes = {'ReactionBounds': reaction_bounds, 'DynamicFBA': dynamic_fba}
    topology = {
        'ReactionBounds': {
            'reaction_bounds': ('reaction_bounds',),
        },
        'DynamicFBA': {
            'fluxes': ('fluxes_values',),
            'reactions': ('reactions_list',),
            'objective_flux': ('objective_flux_value',),
            'reaction_bounds': ('reaction_bounds',)  # Add this line
        }
    }
    sim = Engine(processes=processes, topology=topology)
    sim.update(simulation_time)
    data = sim.emitter.get_data()
    output = pf(data)
    return data, output, processes, topology