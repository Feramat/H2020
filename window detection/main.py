import json
import pytz
from datetime import datetime
import pandas as pd
import numpy as np
from plot_signals import plot_signals


def window_open_detection(dt_from, dt_to, class_name, read_from_hdf=True):
    """
    Start algorithm for window open detection. At first read data from SCADA/hdf.
    The results are plotted to class_name.html

    :param datetime dt_from: start time for SCADA data reading
    :param datetime dt_to: end time for SCADA data reading
    :param str class_name: name of the class for open window detection from config file
    :param bool read_from_hdf: if true, read data from hdf
    :return pd.DataFrame: all data needed for windows detection as a DataFrame
    """
    all_data = read_scada_data(dt_from, dt_to, class_name, read_from_hdf)

    all_data = all_data.resample('T').mean()
    all_data = all_data.dropna(how='all')
    all_data = all_data.ffill()
    all_data = all_data.bfill()

    # These constant are adjustable and serve for algorithm tuning
    maw_len = 10  # moving average window length in minutes
    min_open_time = 10  # minimum minutes to be window open
    min_ahu_running = 20  # minimum minutes to be AHU run to detect open window
    min_diff_tin = 3  # minimum temperature diff to detect open window
    min_diff_tout_back = -0.5  # temperature diff to detect close window
    ahu_min_diff = -1  # temperature diff for AHU, for cold AHU start exclusion

    # maximum two minutes in a row can be interpolated
    all_data = all_data.resample('T').mean().interpolate(limit=10)
    all_data['P_ahu'] = all_data['P_ahu'].interpolate(limit=30)
    all_data = all_data.tz_convert(pytz.timezone('Europe/Prague'))

    # Calculate moving average for T_in
    all_data['T_in_ma'] = all_data['T_in'].rolling(maw_len, win_type='triang').mean()
    all_data['T_out_ma'] = all_data['T_out'].rolling(maw_len, win_type='triang').mean()

    all_data['diff_Tout'] = all_data['T_in_ma'] - all_data['T_out_ma']
    all_data['diff_Tin'] = all_data['T_in_ma'] - all_data['T_in']
    all_data['diff_tahu'] = all_data['T_ahu'] - all_data['T_in']

    all_data['win_open'] = 0

    win_open = 0  # number of minutes to be window currently open
    t_in_open = 22
    ahu_running = 0
    ahu_not_running = 0

    for idx in all_data.index:
        if all_data.loc[idx, 'P_ahu'] > 0:
            ahu_running += 1
            ahu_not_running = 0
        else:
            ahu_running = 0
            ahu_not_running += 1

        if win_open > 0:
            if all_data.loc[idx, 'T_in'] - t_in_open > min_diff_tout_back and win_open >= min_open_time:
                win_open = 0
            else:
                all_data.loc[idx, 'win_open'] = 1

        diff_tin = all_data.loc[idx, 'diff_Tin']
        diff_tinout = all_data.loc[idx, 'diff_Tout']
        diff_tahu = all_data.loc[idx, 'diff_tahu']

        if pd.isna(diff_tahu):
            diff_tahu = np.inf

        if pd.isna(diff_tinout):
            continue

        # Calculated t threshold - difference between T_in and T_in,ma to detect open windows
        t_th = np.interp(diff_tinout, [3, 8, 10, 12], [0.3, 0.4, 0.5, 0.7])

        if (diff_tin > t_th) and (diff_tinout > min_diff_tin) and diff_tahu > ahu_min_diff and \
                6 <= idx.hour <= 20 and (ahu_running > min_ahu_running or ahu_running == 0) and win_open == 0:
            # if the windows are closed and opening is detected
            all_data.loc[idx, 'win_open'] = 1
            t_in_open = all_data.loc[idx, 'T_in']  # indoor temperature when opening the window

        if all_data.loc[idx, 'win_open'] == 1:
            win_open += 1

    all_data['win_open'] = all_data['win_open'] * 25  # to be the graphs more representative
    all_data.loc[all_data['win_open'] == 0, 'win_open'] = 22  # to be the graphs more representative
    # plot_signals(all_data[['T_in', 'T_ahu', 'win_open']], outfile=class_name + '.html')
    plot_signals(all_data[['T_in', 'T_ahu', 'win_open', 'T_out', 'P_ahu']], outfile=class_name + '.html')


def read_scada_data(dt_from, dt_to, class_name, read_from_hdf=True, conf_fn='config.json'):
    """
    Download data from SCADA using MERVIS client or return the simulation data from hdf file

    :param datetime dt_from: start time for SCADA data reading
    :param datetime dt_to: end time for SCADA data reading
    :param str class_name: name of the class to be the data downloaded from Mervis. Must correspond to key in json file.
    :param bool read_from_hdf: if true, read data from hdf and not from SCADA
    :param str conf_fn: full path to config file with SCADA parameters, default config.json
    :return pd.DataFrame: all data needed for windows detection as a DataFrame
    """

    if read_from_hdf:
        all_data = pd.read_hdf(class_name + '.hdf')
    else:
        with open(conf_fn, 'r') as fh_conf:
            conf = json.load(fh_conf)

        usr = conf['scada_params']['username']
        psw = conf['scada_params']['password']
        url = conf['scada_params']['url']
        project_id = conf['scada_params']['project_id']

        tout_guid = conf['variables'][class_name]['t_out']
        tin_guid = conf['variables'][class_name]['t_in']
        ahu_fan_guid = conf['variables'][class_name]['ahu_fan']
        t_supply = conf['variables'][class_name]['t_supply']

        list_guids = [tin_guid, tout_guid, t_supply, ahu_fan_guid]
        list_cols = ['T_in', 'T_out', 'T_ahu', 'P_ahu']

        from ScadaClient3 import ScadaClient
        sc = ScadaClient(url, usr, psw)

        raw_data = sc.get_history(project_id, list_guids, dt_from, dt_to)
        all_data = pd.DataFrame()

        for idx, guid in enumerate(list_guids):
            guid_s = pd.Series(
                name=list_cols[idx], index=raw_data[guid]['raw']['tx_dt'], data=raw_data[guid]['raw']['values']
            )

            all_data = all_data.combine_first(pd.DataFrame(guid_s))

        all_data.index = all_data.index.map(lambda x: x.replace(microsecond=0))
        all_data.to_hdf(class_name + '.hdf', 'libeznice', mode='w')
        print('All data successfully downloaded from Mervis DB.')
    all_data = all_data.loc[(all_data.index >= dt_from) & (all_data.index <= dt_to), :]
    return all_data


if __name__ == '__main__':
    dt_st = datetime(2019, 12, 1, 0, tzinfo=pytz.utc)
    dt_t = datetime(2019, 12, 30, 0, 0, tzinfo=pytz.utc)
    window_open_detection(dt_st, dt_t, 'class_01', read_from_hdf=True)
