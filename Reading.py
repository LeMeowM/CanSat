import csv
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

# File path to your CSV file
file_path = "example.csv"

# Initialize an empty list to store the rows
data = []

# Open the CSV file and read its contents
with open(file_path, newline="", encoding="utf-8") as csvfile:
    csvreader = csv.reader(csvfile)  # Create a CSV reader
    for row in csvreader:
        data.append(row)  # Add each row to the 2D list
fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")
for vector in data:
    R = 6371
    lon_rad = np.radians(float(vector[0]))
    lat_rad = np.radians(float(vector[1]))

    x = (R + float(vector[2])) * np.cos(lat_rad) * np.cos(lon_rad)
    y = (R + float(vector[2])) * np.cos(lat_rad) * np.sin(lon_rad)
    z = (R + float(vector[2])) * np.sin(lat_rad)

    v = np.array([x, y, z])
    vlength = np.log10(np.linalg.norm(v))
    ax.quiver(
        x + 1200,
        y - 5600,
        z - 2700,
        float(vector[3]),
        float(vector[4]),
        float(vector[5]),
        pivot="tail",
        length=vlength,
        arrow_length_ratio=0.3 / vlength,
    )
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.set_zlabel("z")
plt.show()
# Display the 2D array (list of lists)
print("data")
