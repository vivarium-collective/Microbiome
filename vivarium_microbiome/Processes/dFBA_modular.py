from RegulatoryProtein import RegulatoryProtein
from GeneExpression import GeneExpression
from ProteinExpression import ProteinExpression
from ReactionBounds import ReactionBounds
from DynamicFBA import DynamicFBA
from BiomassCalculator import BiomassCalculator
from EnvCalculator import EnvCalculator
from vivarium.core.process import Process, Step
from vivarium.core.engine import Engine, pf
from cobra.io import read_sbml_model
import random


TIME_PROPORTION = (1 / 60)  # we set each time-step as an hour and the Time_proportion as a minute




# ...



def main(config):
    """
    This function runs the simulation for a specified duration.

    It initializes the ReactionBounds, DynamicFBA, BiomassCalculator, EnvCalculator,
    RegulatoryProtein, GeneExpression and ProteinExpression processes,
    establishes the topology between these processes, and executes the simulation for the specified timeframe.
    """
    initial_state = config['main']['initial_state']
    simulation_time = config['main']['simulation_time']
    reaction_bounds = ReactionBounds(config['ReactionBounds'])
    dynamic_fba = DynamicFBA(config['DynamicFBA'])
    initial_state = {"reaction_bounds": reaction_bounds.bounds}
    initial_objective_flux_update = dynamic_fba.next_update(1, initial_state)
    initial_objective_flux = initial_objective_flux_update["objective_flux"]
    biomass_calculator = BiomassCalculator({'initial_objective_flux': initial_objective_flux})
    env_calculator = EnvCalculator(config['EnvCalculator'])
    regulatory_protein = RegulatoryProtein(config['RegulatoryProtein'])
    gene_expression = GeneExpression(config['GeneExpression'])
    protein_expression = ProteinExpression(config['ProteinExpression'])

    processes = {
        'ReactionBounds': reaction_bounds,
        'DynamicFBA': dynamic_fba,
        'BiomassCalculator': biomass_calculator,
        'EnvCalculator': env_calculator,
        'RegulatoryProtein': regulatory_protein,
        'GeneExpression': gene_expression,
        'ProteinExpression': protein_expression
    }

    topology = {
        'ReactionBounds': {
            'reaction_bounds': ('reaction_bounds',),
            'current_v0': ('current_v0',),
            'concentration': ('concentration',),
            'enz_concentration': ( 'enz_concentration',)
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
            'concentration': ('concentration',)
        },
        'RegulatoryProtein': {
            'regulation_probability': ('regulation_probability',)
        },
        'GeneExpression': {
            'regulation_probability': ('regulation_probability',),
            'gene_expression': ('gene_expression',)
        },
        'ProteinExpression': {
            'gene_expression': ('gene_expression',),
            'enz_concentration': ('enz_concentration',)
        }
    }

    sim = Engine(processes=processes, topology=topology, initial_state=initial_state)
    sim.update(simulation_time)
    data = sim.emitter.get_data()
    output = pf(data)
    return data, output, processes, topology