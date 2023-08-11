import numpy as np

def Meshgrid2Ascii(text_file, XX, YY, ZZ, nodata):
    nrows, ncols = ZZ.shape

    cellsize = XX[0, 1] - XX[0, 0]
    xmin = np.min(XX) - cellsize / 2
    ymin = np.min(YY) - cellsize / 2

    # Write file
    with open(text_file, 'w') as f:
        # header
        f.write(f'ncols {ncols}\nnrows {nrows}\n')
        f.write(f'xllcorner {xmin:.12f}\nyllcorner {ymin:.12f}\n')
        f.write(f'cellsize {cellsize:.12f}\nNODATA_value {nodata}\n')

        # data
        ZZ = np.flipud(ZZ)
        ZZ[np.isnan(ZZ)] = nodata

        for row in ZZ:
            row_str = ' '.join(map(str, row))
            f.write(row_str + '\n')
