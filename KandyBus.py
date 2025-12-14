import simpy
import statistics
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# LOAD DATA

data = pd.read_csv("221438210_Deliverable01_data_Set.csv")

# Convert arrival time to datetime
data["Actual_Arrival"] = pd.to_datetime(data["Actual_Arrival"], format="%H:%M")

# Sort buses by arrival time
data = data.sort_values("Actual_Arrival").reset_index(drop=True)

# PREPARE ARRIVAL TIMES

start_time = data["Actual_Arrival"].min()
data["Arrival_Min"] = (
    data["Actual_Arrival"] - start_time
).dt.total_seconds() / 60

SIM_TIME = int(data["Arrival_Min"].max() + 60)

# SIMULATION PARAMETERS

num_service_units = int(input("Enter number of service units at bus stop: "))

waiting_times = []
service_times = []
total_times = []

# SIMPY ENVIRONMENT

env = simpy.Environment()
service_units = simpy.Resource(env, capacity=num_service_units)

# BUS PROCESS

def bus(env, passengers):
    arrival = env.now

    with service_units.request() as req:
        yield req
        start_service = env.now

        # Waiting time
        waiting_times.append(start_service - arrival)

        # Boarding / service time (minutes)
        service_time = passengers * 0.3
        service_times.append(service_time)

        yield env.timeout(service_time)

        # Total time in system
        total_times.append(env.now - arrival)

# BUS STOP PROCESS

def bus_stop(env, dataset):
    for _, row in dataset.iterrows():
        yield env.timeout(row["Arrival_Min"] - env.now)
        env.process(bus(env, row["Passenger_Count"]))

# RUN SIMULATION

env.process(bus_stop(env, data))
env.run(until=SIM_TIME)

# SAFE MEAN FUNCTION

def safe_mean(values):
    return statistics.mean(values) if values else 0

# RESULTS

print("\n--- Kandy Public Bus Network Performance Results ---")
print("Service Units at Stop:", num_service_units)
print("Total Bus Arrivals:", len(total_times))
print(f"Average Waiting Time at Stop: {safe_mean(waiting_times):.2f} mins")
print(f"Average Boarding Time: {safe_mean(service_times):.2f} mins")
print(f"Average Total Time at Stop: {safe_mean(total_times):.2f} mins")

# VISUALIZATIONS

output_dir = Path("graphs")
output_dir.mkdir(exist_ok=True)

# 1️ Waiting Time Trend (Detailed Analysis)
plt.figure()
plt.plot(waiting_times)
plt.xlabel("Bus Arrival Index")
plt.ylabel("Waiting Time (minutes)")
plt.title("Waiting Time Trend at Bus Stop")
plt.tight_layout()
plt.savefig(output_dir / "waiting_time_trend.png")
plt.close()

# 2️ Waiting Time Histogram (Queueing Behavior)
plt.figure()
plt.hist(waiting_times, bins=15)
plt.xlabel("Waiting Time (minutes)")
plt.ylabel("Frequency")
plt.title("Distribution of Waiting Times")
plt.tight_layout()
plt.savefig(output_dir / "waiting_time_histogram.png")
plt.close()

# 3️ Service Time Distribution (Service Rate Analysis)
plt.figure()
plt.hist(service_times, bins=15)
plt.xlabel("Service Time (minutes)")
plt.ylabel("Frequency")
plt.title("Distribution of Boarding Times")
plt.tight_layout()
plt.savefig(output_dir / "service_time_distribution.png")
plt.close()

# 4️ Passenger Count vs Waiting Time (Bottleneck Identification)
plt.figure()
plt.scatter(
    data["Passenger_Count"][:len(waiting_times)],
    waiting_times
)
plt.xlabel("Passenger Count")
plt.ylabel("Waiting Time (minutes)")
plt.title("Passenger Demand vs Waiting Time")
plt.tight_layout()
plt.savefig(output_dir / "passenger_vs_waiting.png")
plt.close()

print("\nAll graphs saved in the 'graphs' folder.")
