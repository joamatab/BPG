from shapely.geometry import Polygon, MultiPolygon
from typing import Union, Tuple, List
from math import ceil, sqrt
import sys

MAX_POINTS = sys.maxsize


# from figures import SIZE, BLUE, GRAY, set_limits
def plot_coords(ax, x, y, color='#999999', zorder=1):
    ax.plot(x, y, 'o', color=color, zorder=zorder)


def plot_line(ax, ob, color='r'):
    parts = hasattr(ob, 'geoms') and ob or [ob]
    for part in parts:
        x, y = part.xy
        ax.plot(x, y, color=color, linewidth=3, solid_capstyle='round', zorder=1)


def coords_apprx_in_line(coord1,  # type: Tuple[float, float]
                         coord2,  # type: Tuple[float, float]
                         coord3,  # type: Tuple[float, float]
                         eps_grid=1e-4,  # type: float
                         ):
    """
    Tell if three coordinates are in the same line
    Expected to have three consecutive coordinates as inputs when the function is called
    """
    dx1_2 = coord1[0] - coord2[0]
    dy1_2 = coord1[1] - coord2[1]
    dx2_3 = coord2[0] - coord3[0]
    dy2_3 = coord2[1] - coord3[1]

    # if any of the two consecutive coords are actually the same, the three coords are in a line
    if ((abs(dx1_2) < eps_grid) and (abs(dy1_2) < eps_grid)) or ((abs(dx2_3) < eps_grid) and (abs(dy2_3) < eps_grid)):
        return True
    else:
        # if x&y coords are accurate, we should have dx1_acc * dy2_acc =dx2_acc * dy1_acc,
        # because of inaccuracy in float numbers, we have
        # |dx1 * dy2 - dx2 * dy1| = |(dx1_acc + err1) * (dy2_acc + err2) - (dx2_acc + err3) * (dy1_acc + err4)|
        #                         ~ |dx1 * err2 + dy2 * err1 - dx2 * err4 - dy1 * err3|
        #                         < sum(|dx1|, |dx2|, |dy1|, |dy2|) * |err_max|
        error_abs = abs(dx1_2 * dy2_3 - dx2_3 * dy1_2)
        error_rlt = error_abs / (abs(dx1_2) + abs(dx2_3) + abs(dy1_2) + abs(dy2_3))
        return error_rlt < eps_grid


def cleanup_loop(coords_list_ori,  # type: List[Tuple[float, float]]
                 eps_grid=1e-4,  # type: float
                 ):

    # once a coordinate is deleted from the coords list, set fully_cleaned to False
    fully_cleaned = True

    # append the first two coords in the origin list to a new list
    coords_list_out = [coords_list_ori[0], coords_list_ori[1]]

    # if the last coord in the new list has the same x or y coordinate with
    # both the second last coord and the coord to append, delete this coord
    coord_1stlast = coords_list_out[-1]
    coord_2ndlast = coords_list_out[-2]
    # print(len(coords_list_ori))
    for i in range(2, len(coords_list_ori)):
        coord_to_append = coords_list_ori[i]
        if coords_apprx_in_line(coord_2ndlast, coord_1stlast, coord_to_append, eps_grid=eps_grid):
            fully_cleaned = False
            coords_list_out = coords_list_out[:-1]
            coords_list_out.append(coord_to_append)
            coord_1stlast = coord_to_append
        else:
            coords_list_out.append(coord_to_append)
            coord_2ndlast = coord_1stlast
            coord_1stlast = coord_to_append

    # print('coord_list_out', coords_list_out)
    # now all the coordinates except the first and the last (the same one) should be on a corner of the polygon,
    # unless the following appended coord has been deleted
    # check if the firsr&last coord is redundant
    if coords_apprx_in_line(coords_list_out[-2], coords_list_out[0], coords_list_out[1], eps_grid=eps_grid):
        fully_cleaned = False
        coords_list_out = coords_list_out[1:-1]
        coords_list_out.append(coords_list_out[0])

    # LAST STEP: just in case that the first and the last coord are slightly different
    coords_list_out = coords_list_out[0:-1]
    coords_list_out.append(coords_list_out[0])

    return {'coords_list_out': coords_list_out, 'fully_cleaned': fully_cleaned}


def coords_cleanup(coords_list_ori,  # type: List[Tuple[float, float]]
                   eps_grid=1e-4,   # type: float
                   debug=False,  # type: bool
                   ):

    """
    clean up coordinates in the list that are redundant or harmful for following Shapely functions

    Parameters
    ----------
    coords_list_ori : list[tuple[float, float]]
        list of coordinates that enclose a polygon
    eps_grid : float
        a size smaller than the resolution grid size,
        if the difference of x/y coordinates of two points is smaller than it,
        these two points should actually share the same x/y coordinate
    debug : bool
    """
    if debug:
        print('coord_list_ori', coords_list_ori)

    fully_cleaned = False
    coords_list_out = coords_list_ori

    # in some cases, some coordinates become on the line if the following coord is deleted,
    # need to loop until no coord is deleted during one loop
    while not fully_cleaned:
        cleaned_result = cleanup_loop(coords_list_out, eps_grid=eps_grid)
        coords_list_out = cleaned_result['coords_list_out']
        fully_cleaned = cleaned_result['fully_cleaned']

    return coords_list_out


def manh_skill(poly_coords,     # type: List[Tuple[float, float]]
               manh_grid_size,  # type: float
               manh_type,       # type: str
               ):

    """
    Convert a polygon into the polygon with orthogonal edges,
    detailed flavors are the same as it is in the SKILL code


    Parameters
    ----------
    poly_coords : list[tuple[float, float]]
        list of coordinates that enclose a polygon
    manh_grid_size : float
        grid size for manhattanization, edge length after manhattanization should be larger than it
    manh_type : str
        'inc' : the manhattanized polygon is larger compared to the one on the manh grid
        'dec' : the manhattanized polygon is smaller compared to the one on the manh grid
        'non' : additional feature, only map the coords to the manh grid but do no manhattanization
    """

    # Snapping original coordinates to manhattan grid (by rounding)

    def apprx_equal(float1: float,
                    float2: float,
                    eps_grid: float = 1e-9
                    ):
        return abs(float1 - float2) < eps_grid

    def apprx_equal_coord(coord1: Tuple[float, float],
                          coord2: Tuple[float, float],
                          eps_grid: float = 1e-9
                          ):
        return apprx_equal(coord1[0], coord2[0], eps_grid) and (apprx_equal(coord1[1], coord2[0], eps_grid))

    # map the coordinates to the manh grid
    poly_coords_manhgrid = []  # type: List[Tuple[float, float]]
    for coord in poly_coords:
        xcoord_manhgrid = manh_grid_size * round(coord[0] / manh_grid_size)
        ycoord_manhgrid = manh_grid_size * round(coord[1] / manh_grid_size)
        poly_coords_manhgrid.append((xcoord_manhgrid, ycoord_manhgrid))

    # adding the first point to the last if polygon is not closed
    if not apprx_equal_coord(poly_coords_manhgrid[0], poly_coords_manhgrid[-1]):
        poly_coords_manhgrid.append(poly_coords_manhgrid[0])

    # do manhattanization if manh_type is 'inc'
    if manh_type == 'non':
        return poly_coords  # coords_cleanup(poly_coords_manhgrid)
    elif (manh_type == 'inc') or (manh_type == 'dec'):
        # Determining the coordinate of a point which is likely to be inside the convex envelope of the polygon
        # (a kind of "center-of-mass")
        xcoord_sum = 0.0  # type: float
        ycoord_sum = 0.0  # type: float
        for coord_manhgrid in poly_coords_manhgrid:
            xcoord_sum = xcoord_sum + coord_manhgrid[0]
            ycoord_sum = ycoord_sum + coord_manhgrid[1]
        xcoord_in = xcoord_sum / len(poly_coords_manhgrid)
        ycoord_in = ycoord_sum / len(poly_coords_manhgrid)
        # print("point INSIDE the shape (x,y) =  (%f, %f)" %(xcoord_in, ycoord_in))

        # Scanning all the points of the orinal list and adding points in-between.
        poly_coords_orth = [poly_coords_manhgrid[0]]
        # print('len(poly_coords_manhgrid)', len(poly_coords_manhgrid))
        for i in range(0, len(poly_coords_manhgrid) - 1):
            # BE CAREFUL HERE WITH THE INDEX
            coord_curr = poly_coords_manhgrid[i]
            if i == len(poly_coords_manhgrid) - 1:
                coord_next = coord_curr
            else:
                coord_next = poly_coords_manhgrid[i+1]

            delta_x = coord_next[0] - coord_curr[0]
            delta_y = coord_next[1] - coord_curr[1]
            eps_float = 1e-9
            # current coord and the next coord create an orthogonal edge
            if (abs(delta_x) < eps_float) or (abs(delta_y) < eps_float):
                # print("This point has orthogonal neighbour", coord_curr, coord_next)
                poly_coords_orth.append(coord_next)
            else:
                if abs(delta_x) > abs(delta_y):
                    num_point_add = int(abs(round(delta_y / manh_grid_size)))
                    xstep = round(delta_y/abs(delta_y)) * manh_grid_size * (delta_x/delta_y)
                    ystep = round(delta_y/abs(delta_y)) * manh_grid_size
                else:
                    num_point_add = int(abs(round(delta_x / manh_grid_size)))
                    ystep = round(delta_x / abs(delta_x)) * manh_grid_size * delta_y / delta_x
                    xstep = round(delta_x / abs(delta_x)) * manh_grid_size
                # if positive, the center if the shape is on the left
                vec_product1 = xstep * (ycoord_in - coord_curr[1]) - ystep * (xcoord_in - coord_curr[0])
                # if positive the vector ( StepX, 0.0) is on the left too
                vec_product2 = xstep * 0.0 - ystep * xstep
                for j in range(0, num_point_add):
                    x0 = coord_curr[0] + j * xstep
                    y0 = coord_curr[1] + j * ystep
                    # If both are positive, incrememnting in X first will make the polygon smaller:
                    # incrememnting X first if manh_type is 'inc'
                    if ((vec_product1 * vec_product2) < 0) == (manh_type == 'inc'):
                        poly_coords_orth.append((x0 + xstep, y0))
                        poly_coords_orth.append((x0 + xstep, y0 + ystep))
                    # elseincrememnting Y first
                    else:
                        poly_coords_orth.append((x0, y0 + ystep))
                        poly_coords_orth.append((x0 + xstep, y0 + ystep))

        # clean up the coords
        return coords_cleanup(poly_coords_orth)
    else:
        raise ValueError('manh_type = {} should be either "non", "inc" or "dec"'.format(manh_type))


def polyop_manh_polygon(geom,  # type: Polygon
                        manh_grid_size,  # type: float
                        do_manh,  # type: bool
                        ):
    # print(geom)
    if geom.type != 'Polygon':
        raise ValueError('Unhandled geometry type: ' + repr(geom.type) + ', type should be Polygon')

    # if do full manhattanization, enlarge the exterior boundary and shrink the interior one
    if do_manh:
        manh_type_ext = 'inc'
        manh_type_int = 'dec'
    # if only map coords to the manh grid, set manh_type to 'non'
    else:
        manh_type_ext = 'non'
        manh_type_int = 'non'

    # for each Polygon object(not MultiPolygon), first get the exterior shape
    coords_ext_orig = list(zip(*geom.exterior.coords.xy))  # type: List[Tuple[float, float]]
    coords_ext_manh = manh_skill(coords_ext_orig, manh_grid_size, manh_type=manh_type_ext)
    # MUST buffer by 0 since other tools might give another type of coord list
    poly_ext_manh = Polygon(coords_ext_manh).buffer(0, cap_style=3, join_style=2)

    # take poly_ext_manh as the initial poly_manh
    poly_manh = poly_ext_manh
    if len(geom.interiors):
        for interior in geom.interiors:
            # for each interior coord list, convert to polygon, buffer by 0 to clean up, and take a subtraction
            coords_int_orig = list(zip(*interior.coords.xy))  # type: List[Tuple[float, float]]
            coords_int_manh = manh_skill(coords_int_orig, manh_grid_size, manh_type=manh_type_int)
            poly_int_manh = Polygon(coords_int_manh).buffer(0, cap_style=3, join_style=2)

            poly_manh = poly_manh.difference(poly_int_manh)
    else:
        pass

    return poly_manh


def polyop_manh(geom,  # type: Union[Polygon, MultiPolygon]
                manh_grid_size,  # type: float
                do_manh,  # type: bool
                ):
    if geom.type == 'Polygon':
        poly_manh = polyop_manh_polygon(geom, manh_grid_size, do_manh=do_manh)
        return poly_manh
    elif geom.type == 'MultiPolygon':
        poly_manh = polyop_manh_polygon(geom[0], manh_grid_size, do_manh=do_manh)
        for poly_Polygon in geom[1:]:
            poly_manh = poly_manh.union(polyop_manh_polygon(poly_Polygon, manh_grid_size, do_manh=do_manh))
        return poly_manh
    else:
        raise ValueError('Unhandled geometry type: ' + repr(geom.type) +
                         'type should be either "Polygon" or "MultiPolygon"')




