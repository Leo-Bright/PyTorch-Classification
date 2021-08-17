import csv
import json
import pandas as pd
import math
from tqdm import tqdm
from scipy import spatial
from datetime import datetime, timedelta


divideBound = 5
file_count = 0
floatBitNumber = 8

longitudeMin = -74.891
longitudeMax = -73.72294
latitudeMin = 40.52419
latitudeMax = 40.90706
# 网格的划分
widthSingle = 0.01 / math.cos(latitudeMin / 180 * math.pi) / divideBound
width = math.floor((longitudeMax - longitudeMin) / widthSingle)
heightSingle = 0.01 / divideBound
height = math.floor((latitudeMax - latitudeMin) / heightSingle)
print("height = ", height)
print("heightSingle = ", heightSingle)
print("width = ", width)
print("widthSingle = ", widthSingle)


def gen_train_test_data(accident_file_path, weather_file_path, train_samples_path):

    date_format = '%Y/%m/%d %H:%M:%S'

    date_weather_dict = {}
    weather_csv = csv.reader(open(weather_file_path))

    for row in tqdm(weather_csv, "Processing weather data:"):
        key_date = row[0]
        date_weather_dict[key_date] = row[1:]

    samples = []

    crash_csv = csv.reader(open(accident_file_path))
    headers = next(crash_csv)

    # new_headers = ['longitude', 'latitude', 'time', 'result']
    # samples.append(new_headers)

    for row in tqdm(crash_csv, "Generate train data:"):
        longitude = row[0]
        if longitude == None or longitude == '':
            continue
        latitude = row[1]
        if latitude == None or latitude == '':
            continue
        crash_time = row[2]
        _dt = datetime.strptime(crash_time, date_format)
        year, month, day, hour, minute = _dt.year, _dt.month, _dt.day, _dt.hour, _dt.minute
        if minute < 30:
            delta = minute
            p_crash_time = _dt - timedelta(minutes=delta)
        else:
            delta = 60 - minute
            p_crash_time = _dt + timedelta(minutes=delta)
        # add a positive sample
        if p_crash_time.year != 2018:
            continue
        elif p_crash_time.month < 10:
            continue
        p_sample = []
        p_sample.append(1)
        p_sample.append(longitude)
        p_sample.append(latitude)
        p_sample.append(p_crash_time)
        if str(p_crash_time) not in date_weather_dict:
            continue
        p_sample += date_weather_dict[str(p_crash_time)]
        samples.append(p_sample)

        # add negative sample
        n1_crash_time = p_crash_time - timedelta(hours=1)
        if n1_crash_time.month >= 10:
            n1_sample = []
            n1_sample.append(0)
            n1_sample.append(longitude)
            n1_sample.append(latitude)
            n1_sample.append(n1_crash_time)
            if str(n1_crash_time) not in date_weather_dict:
                continue
            n1_sample += date_weather_dict[str(n1_crash_time)]
            samples.append(n1_sample)

        n2_crash_time = p_crash_time - timedelta(hours=2)
        if n2_crash_time.month >= 10:
            n2_sample = []
            n2_sample.append(0)
            n2_sample.append(longitude)
            n2_sample.append(latitude)
            n2_sample.append(n2_crash_time)
            if str(n2_crash_time) not in date_weather_dict:
                continue
            n2_sample += date_weather_dict[str(n2_crash_time)]
            samples.append(n2_sample)

        n3_crash_time = p_crash_time + timedelta(hours=1)
        if n3_crash_time.year <= 2018:
            n3_sample = []
            n3_sample.append(0)
            n3_sample.append(longitude)
            n3_sample.append(latitude)
            n3_sample.append(n3_crash_time)
            if str(n3_crash_time) not in date_weather_dict:
                continue
            n3_sample += date_weather_dict[str(n3_crash_time)]
            samples.append(n3_sample)

        n4_crash_time = p_crash_time + timedelta(hours=2)
        if n4_crash_time.year <= 2018:
            n4_sample = []
            n4_sample.append(0)
            n4_sample.append(longitude)
            n4_sample.append(latitude)
            n4_sample.append(n4_crash_time)
            if str(n4_crash_time) not in date_weather_dict:
                continue
            n4_sample += date_weather_dict[str(n4_crash_time)]
            samples.append(n4_sample)

    train_samples_csv = csv.writer(open(train_samples_path, 'w+', newline=''))
    train_samples_csv.writerows(samples)


def extend_poi_data(train_samples_path, poi_file_path, poi_train_samples_path):

    nodes = pd.read_csv(poi_file_path)
    all_nodes_position_list = list(zip(nodes['XCoord'].tolist(), nodes['YCoord'].tolist()))
    tree_nodes = spatial.KDTree(all_nodes_position_list)

    accident_samples = pd.read_csv(train_samples_path)

    new_accident_samples = []

    for index, row in tqdm(accident_samples.iterrows(), total=accident_samples.shape[0]):
        lon = row[1]
        lat = row[2]
        distance, node_id = tree_nodes.query([lon, lat])
        if distance >= 0.01 / 2:
            print(f"distance {distance}, node_id {node_id}")
            continue
        node_info = nodes.loc[node_id]
        pois = json.loads(node_info['spatial_features'])
        _row = row.values.tolist()
        _row += pois
        new_accident_samples.append(_row)

    new_samples_csv = csv.writer(open(poi_train_samples_path, 'w+', newline=''))
    new_samples_csv.writerows(new_accident_samples)


def extend_speed_data(poi_train_samples_path, speed_file_path, speed_poi_train_samples_path):

    date_format = '%Y-%m-%d %H:%M:%S'

    # speed_data = pd.read_csv(speed_file_path, index_col=0, parse_dates=True)

    date_range = pd.date_range(start="2018-12-30 00:00:00", end="2018-12-31 23:00:00", freq="1H")
    date_range_dict = {}
    for time_idx in date_range:
        date_range_dict[str(time_idx)] = time_idx
    # resampled_speed_data = speed_data.resample(rule="1H").mean()
    # assert date_range[0] in speed_data.index
    # assert date_range[-1] in speed_data.index

    poi_accident_samples = pd.read_csv(poi_train_samples_path)

    for index, row in tqdm(poi_accident_samples.iterrows(), total=poi_accident_samples.shape[0]):
        lon = row[1]
        lat = row[2]
        date = row[3]

        widthIndex = math.floor((lon - longitudeMin) / widthSingle)
        heightIndex = math.floor((lat - latitudeMin) / heightSingle)
        column_idx = str(heightIndex) + "," + str(widthIndex)
        row_idx = date_range_dict[date]
        # speed_data_row = speed_data.loc[]
        # print(speed_data_row)
        print("...")

if __name__ == '__main__':

    accident_file_path = 'data/DSTGCN/accidents_201810_201812.csv'
    speed_file_path = 'data/DSTGCN/all_grids_speed_201810_201812.csv'
    poi_file_path = 'data/DSTGCN/edges_data.h5'
    weather_file_path = 'data/DSTGCN/weather.csv'

    train_samples_path = 'data/DSTGCN/train_samples.csv'
    poi_train_samples_path = 'data/DSTGCN/poi_train_samples.csv'
    speed_poi_train_samples_path = 'data/DSTGCN/speed_poi_train_samples.csv'

    # gen_train_test_data(accident_file_path, weather_file_path, train_samples_path)

    # extend_poi_data(train_samples_path, poi_file_path, poi_train_samples_path)

    extend_speed_data(poi_train_samples_path, speed_file_path, speed_poi_train_samples_path)

