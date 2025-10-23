# Inherited CRSes with primvars

This builds on Simon's `poc_user_crs_class_inheritance` by putting the CRS WKT into
a primvar so that it is automatically inherited by all child prims. In this case,
this means that the `</World/NewYork/MoMA/>` and `</World/NewYork/MoMa/MoMaBuilding>` prims
both inherit the WKT of the CRS.

The `NewYork` prim gets its CRS from the class it inherits from, not from its parent prim, which is
the behavior we are looking for.

The python script is also updated to be a standalone script. Running it with `uv run geodemo.py` will
automatically create an isolated environment to run the script.