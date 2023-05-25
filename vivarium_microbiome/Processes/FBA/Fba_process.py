from vivarium.core.process import Process
from vivarium.core.engine import Engine, pf
import numpy as np

from cobra.io import read_sbml_model
from cobra.util import create_stoichiometric_matrix

class FBA(Process):
    defaults = {}
    def __init__(self, parameters = None):
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

    def next_update(self, timestep, state):
        solution = self.model.optimize()
        objective_value = solution.objective_value
        fluxes = solution.fluxes.to_dict()
        return {
            "fluxes": fluxes,
            "objective_flux": objective_value
        }

def main(model_path):
    total_time = 1
    parameters = {"model_file": model_path}
    fba = FBA(parameters)
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
