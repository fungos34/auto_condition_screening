import random
import string
import numpy as np
import pandas as pd
from tabulate import tabulate

import run_identifier
import duration_calculator
from formatters import format_current, format_voltage, format_flowrate

from loguru import logger

#############################################################################################
################################## Documentation ############################################
#############################################################################################

def get_run_id():
    """Generates a unique ID.
    :returns: string id of format LlPA-5969-urAY-9208
    """
    id=[]
    for _ in range(4):
        id.append(random.choice(string.ascii_letters))
    id.append('-')
    for _ in range(4):
        id.append(str(random.choice(range(10))))
    id.append('-')
    for _ in range(4):
        id.append(random.choice(string.ascii_letters))
    id.append('-')
    for _ in range(4):
        id.append(str(random.choice(range(10))))
    run_id=''.join(id)
    return run_id



def get_documentation(id: int, currents: list, voltages: list, flow_a: list, flow_b: list, max_flow_a: float, max_flow_b: float, dillution_ba: list, charge_values: list, concentrations: list, stady_state_rinsing_factor: list) -> None:
    """Writes out all experimental parameters for double checking and documentation into the log/ directory.
    :param id: Int, the local run number.
    :ouputs: Excel File with named like "233-documentation-LlPA-5969-urAY-9208", where the initial number is the local run number, the tailing code a unique identifier.
    :prints: A formatted Table of all experimental parameters to the terminal.
    """
    run_num = run_identifier.get_run_number()
    # print(f'currents: {CURRENTS}\nvoltages: {VOLTAGES}\n dillutions b/a: {DILLUTION_BA}\ncharge values: {CHARGE_VALUES}\n concentrations: {CONCENTRATIONS}\nstady state factors: {STADY_STATE_RINSING_FACTOR}')
    df = pd.DataFrame({
        "Sample \nNumber": np.arange(start=1, stop=len(currents)+1,step=1).tolist(),
        "Currents \n(mA)": format_current(currents),
        "Voltages \n(V)": format_voltage(voltages),
        "Flow \nRate \nPump A \n(μL/min)": format_flowrate(flow_a,max_flow_a),
        "Flow \nRate \nPump B \n(μL/min)": format_flowrate(flow_b,max_flow_b),
        "Dillution \nB:A": dillution_ba,
        "z-Values \n(F/mol)": charge_values,
        "Sample \nConcentration \n(mol/L)": concentrations,
        "Stady \nstate \nrinsing \nfactor": stady_state_rinsing_factor
    })

    groups=[]
    for i in range(len(charge_values)):
        grouped = df.groupby("z-Values \n(F/mol)").get_group(charge_values[i])
        groups.append(grouped)
    logger.info(f"\n\n{tabulate(df, headers='keys', tablefmt='psql')}\n\n")
    # print(tabulate(df, headers='keys', tablefmt='psql'))
    df.to_excel(f'logs/{run_num}-documentation-{id}.xlsx')
    groups = pd.concat(groups)

def get_prediction(flow_rates_a: list, flow_rates_b: list, plot: bool = True) -> list:
    """Retrieves predictions for the time it takes to finish an experiment at a certain flow rate. 
    This prediciton is setup dependent and may be wrong when the underlying forumlas are nod adapted accordingly.

    :param flow_rates_a: List of flow rates of pump A.
    :param flow_rates_b: List of flow rates of pump B.
    :param plot: Bool, plots the experiment duration when set to True.
    :returns: List of predicted times.
    """
    cummulated_flowrates=duration_calculator.get_cummulated_flows(flow_rates_a,flow_rates_b)
    predicted_times=duration_calculator.get_times(cummulated_flowrates)
    logger.info(f'<<< predicted durations of the experiments (setup1 fitted curve model) in ascending order: {predicted_times} >>>')
    if plot:
        duration_calculator.plot_time_func(cummulated_flowrates)
    return predicted_times