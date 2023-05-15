"""
=============
dFBA Process
Amin Boroomand, UConn Health, 2023
==============
To do: Documentation

"""
from vivarium.core.process import Process
from vivarium.core.engine import Engine, pf
from cobra.io import read_sbml_model

# Add the Time_proportion variable, We consider each time-step a minute
TIME_PROPORTION = (1 / 60)  # we set each time-step as an hour and the Time_proportion as a minute


class ReactionBounds(Process):
    """
    To Do: Documentation

    """
    defaults = {
        'model_file': None,

    }

    def __init__(self, parameters=None):
        super().__init__(parameters=parameters)
        self.model = read_sbml_model(self.parameters['model_file'])
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
                '_updater': 'set'
            },
            "Current_V0": {  # Add Current_V0 to the schema #TODO : Lower case
                '_default': 10.0
            }
        }

    def next_update(self, timestep, state):
        # Apply 10% reaction_bound_change, it can be any function the user wants
        percentage = 0.001
        updated_bounds = {}
        Current_V0 = state['Current_V0']  #TODO:take care of it

        if timestep == 0:
            updated_bounds = self.bounds
        else:
            current_bounds = state["reaction_bounds"]  # Use the current state's bounds
            for reaction_id, old_bounds in current_bounds.items():
                new_lower_bound = old_bounds[0] * (1 - (percentage * timestep))
                new_upper_bound = old_bounds[1] * (1 - (percentage * timestep))
                if reaction_id == "EX_glc__D_e":
                    new_lower_bound = max(new_lower_bound, Current_V0)
                new_bounds = (new_lower_bound, new_upper_bound)
                updated_bounds[reaction_id] = new_bounds

        return {"reaction_bounds": updated_bounds}


class DynamicFBA(Process):
    defaults = {'reaction_bounds': None}

    def __init__(self, parameters=None):
        super().__init__(parameters=parameters)
        self.model = read_sbml_model(self.parameters["model_file"])
        self.reaction_bounds = self.parameters['reaction_bounds']

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


class BiomassCalculator(Process):
    """
    TO do : documentaiton
    """
    defaults = {'initial_objective_flux': None}

    def __init__(self, parameters=None):
        super().__init__(parameters=parameters)
        self.current_biomass = self.parameters['initial_objective_flux'] #TODO make it to parametetrs

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
                "_updater": "set"  #TODO single quite
            }
        }

    def next_update(self, timestep, state):
        objective_flux = state["objective_flux"]
        current_biomass = self.compute_biomass(objective_flux, TIME_PROPORTION)
        return {
            "current_biomass": current_biomass
        }


class Env_Calculator(Process):   #TODO underscore, """
    defaults = {'init_concentration': 11.1,   # Initial concentration in mmol/L
                'volume': 1,                  # Volume in liter
                'Vmax': 10.01,           # mmol gDW^(-1) h^(-1)
                'Km': 0.002111            # initial glucose concentration/1000, For now we consider it a very low number 0.01111 mmol gDW^(-1)

    }

    def __init__(self, parameters=None):
        super().__init__(parameters=parameters)

    def ports_schema(self):
        return {
            "current_biomass": {
                "_default": 0.0,
            },
            "fluxes_values": {
                "_default": {}
            },
            "current_env_consumption": {
                "_default": 0.0,
                "_emit": True,
                "_updater": "accumulate",
            },
            "concentration": {
                "_default": self.parameters['init_concentration'],
                "_emit": True,
                "_updater": "accumulate",
            },
            "Current_V0": {  # Add Current_V0 to the schema  #TODO capitol and single qui
                "_default": 10.0,
                "_emit": True,
                "_updater": "set",
            }
        }

    def next_update(self, timestep, state):
        current_biomass = state["current_biomass"]
        concentration = state["concentration"]
        fluxes_values = state["fluxes_values"]
        env_consumption = 0
        if "EX_glc__D_e" in fluxes_values:
            env_consumption = (
                    current_biomass * fluxes_values["EX_glc__D_e"] * TIME_PROPORTION
            )
        # Calculate concentration
        delta_C = env_consumption / self.parameters['volume']
        concentration -= abs(delta_C)
        # Calculate Current_V0
        Current_V0 = self.parameters['Vmax'] * concentration / (self.parameters['Km'] + concentration)  #TODO lower case

        return {
            "current_env_consumption": env_consumption,
            "concentration": -abs(delta_C),  # Emit the updated concentration
            "Current_V0": Current_V0  # Emit the calculated Current_V0
        }


def main(model_path, simulation_time):
    parameters = {"model_file": model_path}
    reaction_bounds = ReactionBounds(parameters)
    parameters['reaction_bounds'] = reaction_bounds
    dynamic_fba = DynamicFBA(parameters)

    # We use these lines to pass the initial_objective_flux to Biomass_Calculator
    initial_state = {"reaction_bounds": reaction_bounds.bounds}
    initial_objective_flux_update = dynamic_fba.next_update(1, initial_state)
    initial_objective_flux = initial_objective_flux_update["objective_flux"]
    parameters["initial_objective_flux"] = initial_objective_flux
    biomass_calculator = BiomassCalculator(parameters)
    env_calculator = Env_Calculator(parameters)
    processes = {
        'ReactionBounds': reaction_bounds,
        'DynamicFBA': dynamic_fba,
        'BiomassCalculator': biomass_calculator,
        'EnvCalculator': env_calculator
    }

    topology = {
        'ReactionBounds': {
            'reaction_bounds': ('reaction_bounds',),
            'Current_V0': ('Current_V0',)
        },
        'DynamicFBA': {
            'fluxes': ('fluxes_values',),
            'reactions': ('reactions_list',),
            'objective_flux': ('objective_flux_value',),
            'reaction_bounds': ('reaction_bounds',)
        },
        'BiomassCalculator': {
            'objective_flux': ('objective_flux_value',),
            'current_biomass': ('current_biomass_value',)
        },
        'EnvCalculator': {
            'current_biomass': ('current_biomass_value',),
            'fluxes_values': ('fluxes_values',),
            'current_env_consumption': ('current_env_consumption_value',),
            'concentration': ('concentration',),
            'Current_V0': ('Current_V0',)
        }
    }
    sim = Engine(processes=processes, topology=topology)
    sim.update(simulation_time)
    data = sim.emitter.get_data()
    output = pf(data)
    return data, output, processes, topology
