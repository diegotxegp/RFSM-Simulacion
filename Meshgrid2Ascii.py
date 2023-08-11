import numpy as np

def Meshgrid2Ascii(text_file, XX, YY, ZZ, nodata):
    nrows, ncols = ZZ.shape

    cellsize = XX[0, 1] - XX[0, 0]
    xmin = np.min(XX) - cellsize / 2
    ymin = np.min(YY) - cellsize / 2

    # Write file
    with open(text_file, 'w') as fW:
        # header
        fW.write(f'ncols {ncols}\nnrows {nrows}\n')
        fW.write(f'xllcorner {xmin:.12f}\nyllcorner {ymin:.12f}\n')
        fW.write(f'cellsize {cellsize:.12f}\nNODATA_value {nodata}\n')

        # data
        ZZ = np.flipud(ZZ)
        ZZ[np.isnan(ZZ)] = nodata

        # base string format
        ff_base = ['%.3f, '] * ZZ.shape[1]

        for i in range(ZZ.shape[0]):
            # line string format
            ff = ff_base.copy()
            ff[ZZ[0, :] == nodata] = ['%d, ']
            ff = ''.join(ff)
            ff = ff[:-2] + '\n'  # Remove the last comma and add newline
            # write
            fW.write(ff % tuple(ZZ[i, :]))