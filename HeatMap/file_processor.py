# file_processor.py

import os
import numpy as np
import math
from datetime import datetime
import pytz
from django.conf import settings
from datetime import datetime
from datetime import datetime

def parse_obj_file(file_path):
    vertices = []
    faces = []
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith('v '):
                vertices.append(list(map(float, line.split()[1:4])))
            elif line.startswith('f '):
                faces.append([int(i.split('/')[0]) - 1 for i in line.split()[1:]])
    return np.array(vertices), faces

def calculate_polygon_area(vertices):
    if len(vertices) < 3:
        return 0
    x = vertices[:, 0]
    z = vertices[:, 2]
    return 0.5 * np.abs(np.dot(x, np.roll(z, 1)) - np.dot(z, np.roll(x, 1)))

def calculate_cos_theta(latitude, longitude, time):
    timezone = pytz.timezone('Asia/Kolkata')
    dt = timezone.localize(time)
    solar_declination = -23.44 * math.cos(math.radians(360 / 365 * (dt.timetuple().tm_yday + 10)))
    solar_hour_angle = (time.hour - 12) * 15
    cos_theta = (
        math.sin(math.radians(latitude)) * math.sin(math.radians(solar_declination))
        + math.cos(math.radians(latitude)) * math.cos(math.radians(solar_declination))
        * math.cos(math.radians(solar_hour_angle))
    )
    return max(0, cos_theta)

def update_mtl_file(output_path, colors):
    with open(output_path, 'w') as file:
        for i, color in enumerate(colors):
            r, g, b = [int(color[i:i+2], 16) / 255.0 for i in (1, 3, 5)]
            file.write(f"newmtl color_{i}\nKd {r:.2f} {g:.2f} {b:.2f}\n")
        file.write("newmtl black_border\nKd 0.0 0.0 0.0\n")
    return [f"color_{i}" for i in range(len(colors))] + ["black_border"]

def modify_obj_file(vertices, faces, potentials, ranges, obj_path, output_path, materials, mtl_file_name):
    with open(obj_path, 'r') as infile, open(output_path, 'w') as outfile:
        outfile.write(f"mtllib {mtl_file_name}\n")
        face_index = 0
        for line in infile:
            if line.startswith('f '):
                potential = potentials[face_index]
                material_index = np.digitize(potential, ranges, right=True)
                outfile.write(f"usemtl {materials[material_index]}\n")
                face_index += 1
            outfile.write(line)
        for face in faces:
            for i in range(len(face)):
                v1, v2 = face[i], face[(i + 1) % len(face)]
                outfile.write("usemtl black_border\n")
                outfile.write(f"f {v1 + 1} {v2 + 1} {v2 + 1}\n")

def process_3d_model(solar_irradiance, timestamp):
    # Define file paths
    obj_path = os.path.join(settings.MEDIA_ROOT, "model.obj")
    mtl_path = os.path.join(settings.MEDIA_ROOT, "model.mtl")
    updated_obj_path = os.path.join(settings.MEDIA_ROOT, "updated.obj")
    updated_mtl_path = os.path.join(settings.MEDIA_ROOT, "updated.mtl")

    # Constants
    latitude = 23.030357
    longitude = 72.517845
    efficiency = 0.15  # η as 15%
    colors = [
        "#FFD700", "#FFA500", "#FF8C00", "#FF6347", "#FF4500",
        "#FF0000", "#E34234", "#CD5C5C", "#DC143C", "#B22222",
        "#8B0000", "#A52A2A", "#800000", "#660000", "#4B0000"
    ]

    # Main logic
    vertices, faces = parse_obj_file(obj_path)
    areas = [calculate_polygon_area(vertices[face]) for face in faces]
    average_area = np.mean([a for a in areas if a > 0])
    areas = [a if a > 0 else average_area for a in areas]
    cos_theta = calculate_cos_theta(latitude, longitude, timestamp)
    potentials = [a * solar_irradiance * efficiency * cos_theta for a in areas]
    min_potential, max_potential = min(potentials), max(potentials)
    ranges = np.linspace(min_potential, max_potential, 16)[1:]
    materials = update_mtl_file(updated_mtl_path, colors)
    modify_obj_file(vertices, faces, potentials, ranges, obj_path, updated_obj_path, materials, "updated.mtl")

    return updated_obj_path, updated_mtl_path
