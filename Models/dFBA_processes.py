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

        solution = self.model.optimize()
        objective_value = solution.objective_value
        fluxes = solution.fluxes.to_dict()
        return {
            "fluxes": fluxes,
            "objective_flux": objective_value,
            "reaction_bounds": self.bounds
        }


class ReactionBoundUpdater(Process):
    defaults = {
        "reaction_bound_percentage_change": 0.1
    }

    def __init__(self, parameters=None):
        super().__init__(parameters=parameters)
        self.percentage_change = self.parameters["reaction_bound_percentage_change"]

    def ports_schema(self):
        return {
            "reaction_bounds": {
                '_default': {},
                '_emit': True,
                "_updater": "set"
            }
        }

    def next_update(self, timestep, state):
        reaction_bounds = state["reaction_bounds"]

        updated_reaction_bounds = {}
        for reaction_id, (lower_bound, upper_bound) in reaction_bounds.items():
            new_bounds = (lower_bound * (1 - self.percentage_change), upper_bound * (1 - self.percentage_change))
            updated_reaction_bounds[reaction_id] = new_bounds

        return {
            "reaction_bounds": updated_reaction_bounds
        }


def main(model_path, simulation_time):
    parameters = {"model_file": model_path}
    dynamic_fba = DynamicFBA(parameters)
    reaction_bound_updater = ReactionBoundUpdater()
    processes = {'DynamicFBA': dynamic_fba, 'ReactionBoundUpdater': reaction_bound_updater}
    topology = {
        'DynamicFBA': {
            'fluxes': ("fluxes_values",),
            'reactions': ("reactions_list",),
            'objective_flux': ("objective_flux_value",),
            'reaction_bounds': ("reaction_bounds",),
        },
        'ReactionBoundUpdater': {
            'reaction_bounds': ("reaction_bounds",),
        }
    }
    sim = Engine(processes=processes, topology=topology)
    sim.update(simulation_time)
    data = sim.emitter.get_data()
    output = pf(data)
    return data,output, processes, topology
