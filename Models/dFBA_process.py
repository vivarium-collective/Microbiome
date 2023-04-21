from vivarium.core.process import Process
from vivarium.core.engine import Engine, pf
from cobra.io import read_sbml_model


class DynamicFBA(Process):
    defaults = {}

    def __init__(self, parameters=None):
        super().__init__(parameters=parameters)
        self.model = read_sbml_model(self.parameters["model_file"])
        self.uptake_rate = self.parameters["uptake_rate"]
        self.time_step = self.parameters["time_step"]
        self.bounds = self.extract_bounds()

    def extract_bounds(self):
        bounds = {}
        for reaction in self.model.reactions:
            bounds[reaction.id] = (reaction.lower_bound, reaction.upper_bound)
        return bounds

    def ports_schema(self):
        return {
            "biomass": {
                '_default': 0.0,
                '_emit': True,
                "_updater": "set"
            },
            "time_points": {
                '_default': [],
                '_emit': True,
                "_updater": "append"
            },
            "reaction_bounds": {
                '_default': self.bounds,
                '_emit': True,
                "_updater": "set"
            }
        }

    def next_update(self, timestep, state):
        current_time = timestep * self.time_step
        time_points = state["time_points"]
        time_points.append(current_time)

        # Update the bounds from the state
        bounds = state["reaction_bounds"]

        # Update the model's reaction bounds
        for reaction_id, (lower_bound, upper_bound) in bounds.items():
            self.model.reactions.get_by_id(reaction_id).lower_bound = lower_bound
            self.model.reactions.get_by_id(reaction_id).upper_bound = upper_bound

        # Perform FBA
        solution = self.model.optimize()
        growth_rate = solution.objective_value
        new_biomass = state["biomass"] + growth_rate * self.time_step

        # Update the model's growth rate constraints
        self.model.medium = {k: v * (1 + growth_rate * self.time_step) for k, v in self.model.medium.items()}



        return {
            "biomass": new_biomass,
            "time_points": time_points,
            "reaction_bounds": self.bounds
        }

def main(model_path, simulation_time=2, time_step=1):
    parameters = {
        "model_file": model_path,
        "uptake_rate": -10,  # Example uptake rate for now
        "time_step": time_step
    }
    dynamic_fba = DynamicFBA(parameters)
    processes = {'DynamicFBA': dynamic_fba}
    topology = {
        'DynamicFBA': {
            'biomass': ("biomass",),
            'time_points': ("time_points",),
            'reaction_bounds': ("reaction_bounds",),
        }
    }
    sim = Engine(processes=processes, topology=topology)
    sim.update(simulation_time)
    data = sim.emitter.get_data()
    output = pf(data)
    return output


# Set the desired model_path
model_path = "e_coli_core.xml"

# Call the main function with the model_path
output = main(model_path)

# Display the output DataFrame
print(output)
