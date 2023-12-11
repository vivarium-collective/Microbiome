from vivarium.core.process import Process

class ProteinExpression(Process):
    """
    This class multiplies gene_expression by 10.
    """
    defaults = {
        'enz_concentration': 5.0,  #initial value of enz_concentration
    }

    def ports_schema(self):
        return {
            'enz_concentration': {
                '_default': self.parameters['enz_concentration'],
                '_emit': True,
                "_updater": "set"
            },
            'gene_expression': {
                "_updater": "set"
            },
        }

    def next_update(self, timestep, state):
        gene_expression = state['gene_expression']
        enz_concentration = gene_expression * 10
        return {
            'enz_concentration': enz_concentration
        }