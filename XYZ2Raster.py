import numpy as np

def XYZ2Raster(x, y, z):
    # Fill possible missing values in x and y
    ux_raw = np.unique(x)
    uy_raw = np.unique(y)
    
    xdfs = np.unique(np.diff(ux_raw))
    ydfs = np.unique(np.diff(uy_raw))
    
    dx = np.min(xdfs)
    dy = np.min(ydfs)
    
    ux = np.arange(np.min(x), np.max(x) + dx, dx)
    uy = np.arange(np.min(y), np.max(y) + dy, dy)
    
    # Build meshgrid
    XX, YY = np.meshgrid(ux, uy)
    ZZ = np.empty(XX.shape)
    ZZ[:] = np.nan
    
    # Order data
    minx = np.min(x)
    miny = np.min(y)
    
    for ix in range(len(x)):
        j = int((x[ix] - minx) / dx)
        i = int((y[ix] - miny) / dy)
        
        ZZ[i, j] = z[ix]
    
    return XX, YY, ZZ