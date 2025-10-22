#!/usr/bin/env python3
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
def get_crs_projcs(asset_path, folder=None):
    """
    Given an AssetPath to a GeospatialCRS prim in a geospatial USD
    file, open it and extract the projcs string.

    There is probably a more graceful way to do this using the AssetResolver API. This
    approach demonstrates that we can get the WRT string of the CRS, and can cache the
    results.

    Args:
        asset_path (Sdf.AssetPath): Asset path to the geospatial USD file
        folder (str, optional): Folder to prepend to the asset file path.
    Returns:
        str: The projcs string if found, else None
    """
    match = re.match(r"^([^<]*)<([^<>]*)>$", asset_path)
    file_path, prim_path = match.group(1), match.group(2)

    if folder is not None:
        file_path = os.path.join(folder, file_path)

    if not os.path.exists(file_path):
        print(f"Warning: Geospatial USD file '{file_path}' not found.")
        return None

    geo_stage = Usd.Stage.Open(file_path)
    if not geo_stage:
        print(f"Warning: Could not open geospatial USD stage '{file_path}'.")
        return None

    crs_prim = geo_stage.GetPrimAtPath(prim_path)
    if not crs_prim:
        print(f"Warning: CRS prim not found in '{prim_path}'.")
        return None

    projcs_attr = crs_prim.GetAttribute("geolocation:crs:wkt")
    if not (projcs_attr and projcs_attr.HasAuthoredValue()):
        print(f"Warning: 'geolocation:crs:wkt' attribute not found in {prim_path}.")
        return None

    return from_ogc_wkt(projcs_attr.Get())


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

        # Find the prim's CRS
        primvars_api = UsdGeom.PrimvarsAPI(prim)
        crs = primvars_api.FindPrimvarWithInheritance("geolocation:crs")

        if not crs:
            print("  Prim is not georeferenced.")
            continue

        crs_path = crs.Get().path
        crs = get_crs_projcs(crs_path, os.path.dirname(stage_path))
        print(f"  Prim CRS: {crs.name} ({crs_path})")

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
