# Microbiome Multiscale Modeling Project

The Microbiome Multiscale Modeling Project is a research-focused endeavor aimed at building a multiscale understanding
of microbiome through the development and refinement of metabolic analysis techniques. Our focus is on a 
system-level understanding, using computational models to shed light on the complex processes that define the 
interactions within microbial communities. The project employs the [Vivarium](https://vivarium-collective.github.io) 
framework, a tool designed to support the construction and simulation of complex biological systems model.

## Project Outline:

### Flux Balance Analysis (FBA)

We began the project with the implementation of Flux Balance Analysis (FBA) for Escherichia coli, a well-studied model 
organism. FBA is a mathematical procedure used for simulating the metabolism of biological organisms.

[Jupyter Notebook for FBA](https://github.com/vivarium-collective/Microbiome/blob/master/Notebook/FBA.ipynb)

### Dynamic Flux Balance Analysis (dFBA)

Building on our initial implementation, we implemented to Dynamic Flux Balance Analysis (dFBA). dFBA is a time-resolved 
extension of FBA, capable of modeling the flux at each time-step. This advancement enables us to capture and analyze 
the time-dependent behavior of the E. coli's metabolism within the simulated environment.

[Jupyter Notebook for dFBA](https://github.com/vivarium-collective/Microbiome/blob/master/Notebook/dFBA.ipynb)
