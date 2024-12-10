# file_processor.py

import os
import numpy as np
import math
from datetime import datetime
import pytz
from django.conf import settings
from datetime import datetime
from datetime import datetime
import io
from django.core.files.base import ContentFile

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

def update_mtl_file(output_buffer, colors):
    for i, color in enumerate(colors):
        r, g, b = [int(color[i:i+2], 16) / 255.0 for i in (1, 3, 5)]
        output_buffer.write(f"newmtl color_{i}\nKd {r:.2f} {g:.2f} {b:.2f}\n")
    output_buffer.write("newmtl black_border\nKd 0.0 0.0 0.0\n")  # Black border material
    return [f"color_{i}" for i in range(len(colors))] + ["black_border"]


def modify_obj_file(vertices, faces, potentials, ranges, obj_path, output_buffer, materials, mtl_file_name):
    def is_horizontal_face(face_vertices):
        # Check if the face is approximately horizontal by examining the normal vector
        v1 = face_vertices[1] - face_vertices[0]
        v2 = face_vertices[2] - face_vertices[0]
        normal = np.cross(v1, v2)
        return abs(normal[1]) > abs(normal[0]) and abs(normal[1]) > abs(normal[2])  # Y-axis dominance indicates horizontal

    with open(obj_path, 'r') as infile:
        output_buffer.write(f"mtllib {mtl_file_name}\n")  # Reference the material file
        face_index = 0
        unique_edges = set()  # Store unique edges for black borders

        for line in infile:
            if line.startswith('f '):  # Handle face definitions
                face_indices = [int(item.split('/')[0]) - 1 for item in line.split()[1:]]
                face_vertices = vertices[face_indices]

                if is_horizontal_face(face_vertices):  # Check if the face is horizontal
                    potential = potentials[face_index]
                    material_index = np.digitize(potential, ranges, right=True)
                    output_buffer.write(f"usemtl {materials[material_index]}\n")  # Apply colored material
                else:
                    output_buffer.write("usemtl gray\n")  # Apply default gray material for sides

                # Store edges of the current face for borders
                for i in range(len(face_indices)):
                    edge = tuple(sorted([face_indices[i], face_indices[(i + 1) % len(face_indices)]]))
                    unique_edges.add(edge)

                face_index += 1

            output_buffer.write(line)

        # Add edges with black borders
        output_buffer.write("\n# Adding edges with black borders\n")
        output_buffer.write("usemtl black_border\n")
        for edge in unique_edges:
            output_buffer.write(f"l {edge[0] + 1} {edge[1] + 1}\n")  # Add lines representing edges





def process_3d_model(solar_irradiance, timestamp):
    # Define file paths
    obj_path = os.path.join(settings.MEDIA_ROOT, "model.obj")

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

    # In-memory file creation
    obj_buffer = io.StringIO()
    mtl_buffer = io.StringIO()

    # Write updated MTL contents
    materials = update_mtl_file(mtl_buffer, colors)

    # Write updated OBJ contents
    modify_obj_file(vertices, faces, potentials, ranges, obj_path, obj_buffer, materials, "updated.mtl")

    # Convert in-memory content to ContentFile
    obj_file = ContentFile(obj_buffer.getvalue().encode(), name="updated.obj")
    mtl_file = ContentFile(mtl_buffer.getvalue().encode(), name="updated.mtl")

    return obj_file, mtl_file

