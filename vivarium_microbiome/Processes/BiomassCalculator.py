from vivarium.core.process import Process
from cobra.io import read_sbml_model
TIME_PROPORTION = (1 / 60)
class BiomassCalculator(Process):
    """
This class computes the current biomass based on the objective flux.

BiomassCalculator takes in the initial objective flux and estimates the current biomass at each update. The calculation is based on the objective flux, the time proportion, and the current biomass.
"""

    defaults = {'initial_objective_flux': None}

    def __init__(self, parameters=None):
        super().__init__(parameters=parameters)
        self.current_biomass = self.parameters['initial_objective_flux']


    def compute_biomass(self, objective_flux, time_proportion):
        self.current_biomass += objective_flux * time_proportion * self.current_biomass
        return self.current_biomass

    def ports_schema(self):
        return {
            "objective_flux": {
                '_default': 0.0,
                "_updater": "set"
            },
            "current_biomass": {
                '_default': 0.0,
                '_emit': True,
                "_updater": "set"
            }
        }

    def next_update(self, timestep, state):
        objective_flux = state["objective_flux"]
        current_biomass = self.compute_biomass(objective_flux, TIME_PROPORTION)
        return {
            "current_biomass": current_biomass
        }

