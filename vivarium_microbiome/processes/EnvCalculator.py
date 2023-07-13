from vivarium.core.process import Process
TIME_PROPORTION = (1 / 60)
class EnvCalculator(Process):
    """
    This class estimates the environmental consumption (Glucose in this case) and concentration.

    EnvCalculator calculates the environmental consumption using the current biomass and flux values. It also updates the concentration.
    """

    defaults = {
        'init_concentration': 11.1,
        'volume': 10,
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
        }

    def next_update(self, timestep, state):
        current_biomass = state["current_biomass"]
        concentration = state["concentration"]
        fluxes_values = state["fluxes_values"]
        env_consumption = 0
        if "EX_glc__D_e" in fluxes_values:
            env_consumption = (
                    current_biomass * (-fluxes_values["EX_glc__D_e"]) * TIME_PROPORTION
            )
        delta_c = env_consumption / self.parameters['volume']
        concentration += (-delta_c)

        return {
            "current_env_consumption": env_consumption,
            "concentration": - delta_c,
        }

