from vivarium.core.process import Process


class GeneExpression(Process):
    """
    This class multiplies the regulation_probability by 10.
    """
    defaults = {
        'gene_expression': 0.55,  #initial value of gene_expression
    }

    def ports_schema(self):
        return {
            'gene_expression': {
                '_default': self.parameters['gene_expression'],
                '_emit': True,
                "_updater": "set"
            },
            'regulation_probability': {
                '_default': 0.5,
                "_updater": "set"
            },
        }

    def next_update(self, timestep, state):
        regulation_probability = state['regulation_probability']
        gene_expression = regulation_probability * 10/10
        return {
            'gene_expression': gene_expression
        }

