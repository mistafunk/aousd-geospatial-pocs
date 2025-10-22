# DDK OpenUSD Experiments

## Running the code

This repo is set up to work wtih [uv](https://docs.astral.sh/uv/).

## Geolocation

(`/geolocation` folder)

This is an experiment to demonstrate authoring geolocation data
into a prim hierarchy, and then reading the data and transforming
the data into another CRS.

`uv run geolocation/geodemo.py`

### Authoring

Two elements are needed to explicitly georeference a Prim:

1. a `primvar:geospatial:crs` primarvar that contains an asset path to a GeospatialCRS prim. It should have `constant` interpolation.
2. a `!resetXformStack!` op prepended to `xformOpOrder`

### Traversing

When traversing a stage, the crs primvar `primvar:geospatial:crs` will be inherited to all child prims, and can be accessed via `FindPrimvarWithInheritance`.

Since we are reseting the Xform stack whenever we explicitly define a CRS, the local to world
transform returned by `ComputeLocalToWorldTransform` is always relative to the CRS defined in the primvar.

### Transforming

For a given target CRS (hard coded to UTM 17N in this example), we can then transform coordinates from the authored CRS.

### Sample output

Running `uv run geolocation/geodemo.py` gives:

```
USD Geolocation Stage Traversal
========================================
Opening USD stage: /home/daviddekoning/code-wsl/usd/geolocation/geodemo.usda
Successfully opened stage with default prim: /World
------------------------------------------------------------

Prim: /World
  Type: Xform
  Local Transform Operations:
    - xformOp:translate: (708276.91981815, 5706731.7076084, 50)
  Local to World Transform: ( (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (708276.91981815, 5706731.7076084, 50, 1) )
  Prim CRS: WGS 84 / UTM zone 30N (geospatial.usda</Geospatial/UTM30N>)
  Transformed coordinates: (5080928.798402812, 9206849.814173037, 50.0) in target CRS: NAD83 / UTM zone 17N

Prim: /World/NewYork
  Type: Xform
  Local Transform Operations:
    - xformOp:translate: (586000, 4515000, 50)
  Local to World Transform: ( (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (586000, 4515000, 50, 1) )
  Prim CRS: NAD83 / UTM zone 17N (geospatial.usda</Geospatial/UTM17N>)
  Transformed coordinates: (586000.0, 4515000.0, 50.0) in target CRS: NAD83 / UTM zone 17N

Prim: /World/NewYork/MoMa
  Type: Xform
  Local Transform Operations:
    - xformOp:translate: (-393.7, -337.3, 0)
  Local to World Transform: ( (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (585606.3, 4514662.7, 50, 1) )
  Prim CRS: NAD83 / UTM zone 17N (geospatial.usda</Geospatial/UTM17N>)
  Transformed coordinates: (585606.3, 4514662.7, 50.0) in target CRS: NAD83 / UTM zone 17N

Prim: /World/NewYork/MoMa/MoMaBuilding
  Type: Mesh
  No local transform operations.
  Local to World Transform: ( (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (585606.3, 4514662.7, 50, 1) )
  Prim CRS: NAD83 / UTM zone 17N (geospatial.usda</Geospatial/UTM17N>)
  Transformed coordinates: (585606.3, 4514662.7, 50.0) in target CRS: NAD83 / UTM zone 17N
```