from vivarium.core.process import Process
from vivarium.core.engine import Engine, pf
import numpy as np

from cobra.io import read_sbml_model
from cobra.util import create_stoichiometric_matrix


class FBA(Process):
    defaults = {}

    def __init__(self, parameters=None):
        super().__init__(parameters=parameters)
        self.model = read_sbml_model(self.parameters["model_file"])

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
            }
        }

    def set_bounds(self, reaction_id, lower_bound, upper_bound):
        reaction = self.model.reactions.get_by_id(reaction_id)
        reaction.lower_bound = lower_bound
        reaction.upper_bound = upper_bound

    def next_update(self, timestep, state):
        solution = self.model.optimize()
        objective_value = solution.objective_value
        fluxes = solution.fluxes.to_dict()
        return {
            "fluxes": fluxes,
            "objective_flux": objective_value
        }


def main(model_path, reaction_id=None, bounds=None):
    total_time = 1
    parameters = {"model_file": model_path}
    fba = FBA(parameters)

    # Set bounds if both reaction_id and bounds are provided
    if reaction_id is not None and bounds is not None:
        fba.set_bounds(reaction_id, *bounds)

    processes1 = {'FBA': fba}
    topology1 = {
        'FBA': {
            'fluxes': ("fluxes_values", ),
            'reactions': ("reactions_list", ),
            'objective_flux': ("objective_flux_value", )
        }
    }
    sim = Engine(processes=processes1, topology=topology1)
    sim.update(total_time)
    data = sim.emitter.get_data()
    output = pf(data)
    return output, processes1, topology1



