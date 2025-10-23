#!/usr/bin/env -S uv run
#
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "pyproj",
#   "pycrs",
#   "usd-core",
# ]
# ///

"""
OpenUSD script to traverse a stage and print primvars:crs values for each prim.
"""

import os
import re
from functools import lru_cache

import pyproj
from pxr import Usd, UsdGeom
from pycrs.parse import from_ogc_wkt



@lru_cache(maxsize=32)
def get_transformer(from_crs, to_crs):
    """
    Get a pyproj Transformer to convert coordinates from one CRS to another.

    Args:
        from_crs: The source CRS object.
        to_crs: The target CRS object.
    Returns:
        pyproj.Transformer: Transformer object for coordinate conversion.
    """
    return pyproj.Transformer.from_crs(
        from_crs.to_ogc_wkt(), to_crs.to_ogc_wkt(), always_xy=True
    )


def traverse_and_print_geolocation(stage_path, target_crs=None):
    """
    Open a USD stage and traverse all prims to find and print geolocation information.

    Args:
        stage_path (str): Path to the USD file
    """
    # Check if file exists
    if not os.path.exists(stage_path):
        print(f"Error: File '{stage_path}' not found")
        return

    # Open the USD stage
    print(f"Opening USD stage: {stage_path}")
    stage = Usd.Stage.Open(stage_path)

    if not stage:
        print(f"Error: Could not open USD stage '{stage_path}'")
        return

    print(
        f"Successfully opened stage with default prim: {stage.GetDefaultPrim().GetPath()}"
    )
    print("-" * 60)

    # Traverse all prims in the stage
    for prim in stage.Traverse():
        prim_path = prim.GetPath()
        print(f"\nPrim: {prim_path}")
        print(f"  Type: {prim.GetTypeName()}")

        # Print the prim's local and global transforms
        xformable = UsdGeom.Xformable(prim)
        if xformable:
            ops = xformable.GetOrderedXformOps()
            if ops:
                print("  Local Transform Operations:")
                for op in ops:
                    op_name = op.GetOpName()
                    op_value = op.Get()
                    print(f"    - {op_name}: {op_value}")
            else:
                print("  No local transform operations.")
            local_to_world = xformable.ComputeLocalToWorldTransform(
                Usd.TimeCode.Default()
            )
            print(f"  Local to World Transform: {local_to_world}")
        else:
            print("  Not an Xformable prim.")
            continue

        # Find the prim's CRS
        primvars_api = UsdGeom.PrimvarsAPI(prim)
        crs_primvar = primvars_api.FindPrimvarWithInheritance("geolocation:crs:wkt")

        if not crs_primvar:
            print("  Prim is not georeferenced.")
            continue

        crs = from_ogc_wkt(crs_primvar.Get())
        print(f"  Prim CRS: {crs.name}")

        if target_crs:
            # Extract x and y from the world transform matrix
            x = local_to_world[3][0]
            y = local_to_world[3][1]
            z = local_to_world[3][2]
            x_t, y_t = transform(x, y, crs, target_crs)
            print(
                f"  Transformed coordinates: ({x_t}, {y_t}, {z}) in target CRS: {target_crs.name}"
            )


def transform(x, y, from_crs, to_crs):
    """
    Transform a point from one CRS to another.

    Args:
        point (tuple): The (x, y) coordinates to transform.
        from_crs: The source CRS object.
        to_crs: The target CRS object.

    Returns:
        tuple: Transformed (x, y) coordinates.
    """

    transformer = get_transformer(from_crs, to_crs)
    x_t, y_t = transformer.transform(x, y)
    return (x_t, y_t)


def main():
    """Main function to run the CRS primvar traversal."""
    # Path to the USD file (relative to script location)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    usd_file = os.path.join(script_dir, "geodemo.usda")

    print("USD Geolocation Stage Traversal")
    print("=" * 40)

    target_crs = from_ogc_wkt("""PROJCS["NAD83 / UTM zone 17N",
            GEOGCS["NAD83",
                DATUM["North_American_Datum_1983",
                    SPHEROID["GRS 1980",6378137,298.257222101],
                    TOWGS84[0,0,0,0,0,0,0]],
                PRIMEM["Greenwich",0,
                    AUTHORITY["EPSG","8901"]],
                UNIT["degree",0.0174532925199433,
                    AUTHORITY["EPSG","9122"]],
                AUTHORITY["EPSG","4269"]],
            PROJECTION["Transverse_Mercator"],
            PARAMETER["latitude_of_origin",0],
            PARAMETER["central_meridian",-81],
            PARAMETER["scale_factor",0.9996],
            PARAMETER["false_easting",500000],
            PARAMETER["false_northing",0],
            UNIT["metre",1,
                AUTHORITY["EPSG","9001"]],
            AXIS["Easting",EAST],
            AXIS["Northing",NORTH],
            AUTHORITY["EPSG","26917"]]""")

    traverse_and_print_geolocation(usd_file, target_crs=target_crs)


if __name__ == "__main__":
    main()
