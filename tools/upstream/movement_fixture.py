# SPDX-License-Identifier: GPL-3.0-only
"""Generate an original, clear stair route for native controller comparisons.

Only source is distributed. Generated TES3 plugin/COLLADA files belong in the
external evidence directory. Nothing is sampled from a game asset.
"""
import struct


def generate(directory):
    def sub(name, data):
        return name.encode('ascii') + struct.pack('<I', len(data)) + data

    def record(name, data):
        return name.encode('ascii') + struct.pack('<III', len(data), 0, 0) + data

    vertices = []
    triangles = []

    def box(x0, x1, y0, y1, z0, z1):
        base = len(vertices)
        vertices.extend([(x0,y0,z0), (x1,y0,z0), (x1,y1,z0), (x0,y1,z0),
                         (x0,y0,z1), (x1,y0,z1), (x1,y1,z1), (x0,y1,z1)])
        # Outward-facing triangles, including floor and risers.
        for face in ((0,3,2,1), (4,5,6,7), (0,1,5,4),
                     (1,2,6,5), (2,3,7,6), (3,0,4,7)):
            a,b,c,d = (base+i for i in face)
            triangles.extend([(a,b,c), (a,c,d)])

    box(-400,400,-400,0,-20,0)
    for step in range(20):
        box(-200,200,step*24,(step+1)*24,-20,(step+1)*16)
    box(-400,400,480,1100,-20,320)
    positions = ' '.join(str(v) for p in vertices for v in p)
    indices = ' '.join(str(v) for t in triangles for v in t)
    mesh = f'''<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset><unit name="engine_unit" meter="1"/><up_axis>Z_UP</up_axis></asset>
  <library_geometries><geometry id="stairs"><mesh>
    <source id="positions"><float_array id="position-array" count="{len(vertices)*3}">{positions}</float_array>
      <technique_common><accessor source="#position-array" count="{len(vertices)}" stride="3">
        <param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/>
      </accessor></technique_common></source>
    <vertices id="verts"><input semantic="POSITION" source="#positions"/></vertices>
    <triangles count="{len(triangles)}"><input semantic="VERTEX" source="#verts" offset="0"/><p>{indices}</p></triangles>
  </mesh></geometry></library_geometries>
  <library_visual_scenes><visual_scene id="scene"><node id="route"><instance_geometry url="#stairs"/></node></visual_scene></library_visual_scenes>
  <scene><instance_visual_scene url="#scene"/></scene>
</COLLADA>
'''
    (directory / 'meshes').mkdir(parents=True)
    (directory / 'meshes/openoblivion_original_stairs.dae').write_text(mesh)
    header = sub('HEDR', struct.pack('<fi32s256sI', 1.3, 0, b'OpenOblivion contributors',
                                  b'Original controller fixture: 20 steps, rise 16, tread 24.', 2))
    static = sub('NAME', b'oo_original_stairs\0') + sub('MODL', b'openoblivion_original_stairs.dae\0')
    cell = sub('NAME', b'OpenOblivionStairs\0') + sub('DATA', struct.pack('<Iii', 1, 0, 0))
    cell += sub('AMBI', struct.pack('<IIIf', 0x808080, 0x808080, 0x303030, 0.0))
    cell += sub('FRMR', struct.pack('<I', 1)) + sub('NAME', b'oo_original_stairs\0')
    # Place the route far from the origin so the missing-head camera fault
    # satisfies the same recovery condition as the real preview scenes.
    cell += sub('DATA', struct.pack('<6f', 10000, 0, 0, 0, 0, 0))
    (directory / 'original_movement.esp').write_bytes(record('TES3',header)+record('STAT',static)+record('CELL',cell))
