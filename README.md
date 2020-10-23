# Horizon 2020, MPC.- GT Hybrid MPC Geotabs
This repository provides results of the deliverable D3.4 of European Horizon H2020 project titled MPC.- GT Hybrid MPC Geotabs. 
The simulation algorithms for occupancy estimation and open windows detection are included in this repository. The Python libraries pandas, numpy, plotly are necessary to start and plot simulation results. The Python library for MERVIS Scada interface communication (ScadaClient) is not included in this repository but can be obtained on request.

The codes for occupancy estimation algorithm are placed in folder occupancy estimation. The simulation data are stored as pandas DataFrame in the file data_d3_4.hdf. The simulation is started using IPython notebook D3.4_Occupancy.ipynb.

The codes providing open windows detection are placed in folder window detection. 
The simulation script is started using main.py, where the start and end time of simulation is needed to be set. The simulation data must either be stored as pandas DataFrame in hdf file or download from MERVIS using ScadaClient. The example of such a hdf file is in the file class_01.hdf. The configuration file with ScadaClient credentials and variable GUIDS is in config.json. The proper username, password and url must be provided to successfully download the simulation data.  
