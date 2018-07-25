
import gdspy
from typing import Tuple, List, Union  #, TYPE_CHECKING,
from math import ceil  # , floor
from BPG.manh import gdspy_manh  # ,coords_cleanup
import numpy as np
import sys


################################################################################
# define parameters for testing
################################################################################
# TODO: Move numbers into a tech file
global_grid_size = 0.001
global_rough_grid_size = 0.01
global_min_width = 0.1
global_min_space = 0.05
MAX_SIZE = sys.maxsize


def polyop_gdspy_to_point_list(polygon_gdspy_in,  # type: Union[gdspy.Polygon, gdspy.PolygonSet]
                               fracture=True,  # type: bool
                               do_manh=True,  # type: bool
                               manh_grid_size=global_grid_size  # type: float
                               # TODO: manh grid size is magic number
                               ):
    # type: (...) -> List[List[Tuple[float, float]]]
    """

    Parameters
    ----------
    polygon_gdspy_in : Union[gdspy.Polygon, gdspy.PolygonSet]
        The gdspy polygons to be converted to lists of coordinates
    fracture : bool
        True to fracture shapes
    do_manh : bool
        True to perform Manhattanization
    manh_grid_size : float
        The Manhattanization grid size

    Returns
    -------
    output_list_of_coord_lists : List[List[Tuple[float, float]]]
        A list containing the polygon point lists that compose the input gdspy polygon
    """
    if do_manh:
        polygon_gdspy_in = gdspy_manh(polygon_gdspy_in, manh_grid_size=manh_grid_size, do_manh=do_manh)

    if fracture:
        polygon_gdspy = polygon_gdspy_in.fracture(max_points=4094, precision=0.001)  # TODO: Magic numbers
    else:
        polygon_gdspy = polygon_gdspy_in

    output_list_of_coord_lists = []
    if isinstance(polygon_gdspy, gdspy.Polygon):
        output_list_of_coord_lists = [np.round(polygon_gdspy.points, 3)]  # TODO: Magic number?
    elif isinstance(polygon_gdspy, gdspy.PolygonSet):
        for poly in polygon_gdspy.polygons:
            output_list_of_coord_lists.append(np.round(poly, 3))  # TODO: Magic number?
    else:
        raise ValueError('polygon_gdspy must be a gdspy.Polygon or gdspy.PolygonSet')
    return output_list_of_coord_lists


def dataprep_coord_to_gdspy(
        pos_neg_list_list,  # type: Tuple[List[List[Tuple[float, float]]], List[List[Tuple[float, float]]]]
        manh_grid_size,  # type: float
        do_manh,  # type: bool
        ):
    # type: (...) -> Union[gdspy.Polygon, gdspy.PolygonSet]
    """
    Converts list of polygon coordinate lists into GDSPY polygon objects
    The expected input list will be a list of all polygons on a given layer

    Parameters
    ----------
    pos_neg_list_list : Tuple[List, List]
        A tuple containing two lists: the list of positive polygon shapes and the list of negative polygon shapes.
        Each polygon shape is a list of point tuples
    manh_grid_size : float
        The manhattanization grid size
    do_manh : bool
        True to perform Manhattanization

    Returns
    -------
    polygon_out : Union[gdspy.Polygon, gdspy.PolygonSet]
        The gdpsy.Polygon formatted polygons
    """
    pos_coord_list_list = pos_neg_list_list[0]
    neg_coord_list_list = pos_neg_list_list[1]

    polygon_out = gdspy.offset(gdspy.Polygon(pos_coord_list_list[0]),
                               0, tolerance=10, max_points=MAX_SIZE, join_first=True)

    if len(pos_coord_list_list) > 1:
        for pos_coord_list in pos_coord_list_list[1:]:
            polygon_pos = gdspy.offset(gdspy.Polygon(pos_coord_list),
                                       0, tolerance=10, max_points=MAX_SIZE, join_first=True)
            polygon_out = gdspy.offset(gdspy.fast_boolean(polygon_out, polygon_pos, 'or'),
                                       0, tolerance=10, max_points=MAX_SIZE, join_first=True)
    if len(neg_coord_list_list):
        for neg_coord_list in neg_coord_list_list:
            polygon_neg = gdspy.offset(gdspy.Polygon(neg_coord_list),
                                       0, tolerance=10, max_points=MAX_SIZE, join_first=True)
            polygon_out = gdspy.offset(gdspy.fast_boolean(polygon_out, polygon_neg, 'not'),
                                       0, tolerance=10, max_points=MAX_SIZE, join_first=True)

    polygon_out = gdspy_manh(polygon_out, manh_grid_size=manh_grid_size, do_manh=do_manh)
    polygon_out = gdspy.offset(polygon_out, 0, max_points=MAX_SIZE, join_first=True)
    return polygon_out


def dataprep_oversize_gdspy(polygon,  # type: Union[gdspy.Polygon, gdspy.PolygonSet]
                            offset,  # type: float
                            ):
    # type: (...) -> Union[gdspy.Polygon, gdspy.PolygonSet]

    if offset < 0:
        print('Warning: offset = %f < 0 indicates you are doing undersize')
    polygon_oversized = gdspy.offset(polygon, offset, max_points=MAX_SIZE, join_first=True,
                                     join='miter', tolerance=4)
    polygon_oversized = gdspy.offset(polygon_oversized, 0, max_points=MAX_SIZE, join_first=True)

    return polygon_oversized


def dataprep_undersize_gdspy(polygon,  # type: Union[gdspy.Polygon, gdspy.PolygonSet]
                             offset,  # type: float
                             ):
    # type: (...) -> Union[gdspy.Polygon, gdspy.PolygonSet]

    if offset < 0:
        print('Warning: offset = %f < 0 indicates you are doing oversize')
    polygon_undersized = gdspy.offset(polygon, -offset, max_points=MAX_SIZE, join_first=True,
                                      join='miter')
    polygon_undersized = gdspy.offset(polygon_undersized, 0, max_points=MAX_SIZE, join_first=True)
    return polygon_undersized


def dataprep_roughsize_gdspy(polygon,  # type: Union[gdspy.Polygon, gdspy.PolygonSet]
                             size_amount,  # type: float
                             do_manh,  # type: bool
                             ):
    rough_grid_size = global_rough_grid_size

    # oversize twice, then undersize twice and oversize again
    polygon_oo = dataprep_oversize_gdspy(polygon, 2 * rough_grid_size)
    polygon_oouu = dataprep_undersize_gdspy(polygon_oo, 2 * rough_grid_size)
    polygon_oouuo = dataprep_oversize_gdspy(polygon_oouu, rough_grid_size)

    # manhattanize to the rough grid
    polygon_oouuo_rough = gdspy_manh(polygon_oouuo, rough_grid_size, do_manh)

    # undersize then oversize
    polygon_roughsized = dataprep_oversize_gdspy(dataprep_undersize_gdspy(polygon_oouuo_rough, global_grid_size),
                                                 global_grid_size)

    polygon_roughsized = dataprep_oversize_gdspy(polygon_roughsized, max(size_amount - 2 * global_grid_size, 0))

    return polygon_roughsized


def polyop_extend(polygon_toextend,  # type: Union[gdspy.Polygon, gdspy.PolygonSet]
                  polygon_ref,  # type: Union[gdspy.Polygon, gdspy.PolygonSet]
                  extended_amount,  # type: float
                  ):
    grid_size = global_grid_size
    extended_amount = grid_size * ceil(extended_amount / grid_size)
    polygon_ref_sized = dataprep_oversize_gdspy(polygon_ref, extended_amount)
    polygon_extended = dataprep_oversize_gdspy(polygon_toextend, extended_amount)
    polygon_extra = gdspy.offset(gdspy.fast_boolean(polygon_extended, polygon_ref, 'not'),
                                 0, max_points=MAX_SIZE, join_first=True)
    polygon_toadd = gdspy.offset(gdspy.fast_boolean(polygon_extra, polygon_ref_sized, 'and'),
                                 0, max_points=MAX_SIZE, join_first=True)

    polygon_out = gdspy.offset(gdspy.fast_boolean(polygon_toextend, polygon_toadd, 'or'),
                               0, max_points=MAX_SIZE, join_first=True)

    buffer_size = max(grid_size * ceil(0.5 * extended_amount / grid_size + 1.1), 0.0)
    polygon_out = dataprep_oversize_gdspy(dataprep_undersize_gdspy(polygon_out, buffer_size), buffer_size)

    return polygon_out


def poly_operation(polygon1,  # type: Union[gdspy.Polygon, gdspy.PolygonSet, None]
                   polygon2,  # type: Union[gdspy.Polygon, gdspy.PolygonSet, None]
                   operation,  # type: str
                   size_amount,  # type: float
                   do_manh=False,  # type: bool
                   ):
    # type: (...) -> Union[gdspy.Polygon, gdspy.PolygonSet]
    """

    Parameters
    ----------
    polygon1 : Union[gdspy.Polygon, gdspy.PolygonSet, None]
        The shapes currently on the output layer
    polygon2 : Union[gdspy.Polygon, gdspy.PolygonSet, None]
        The shapes on the input layer that will be added/subtracted to/from the output layer
    operation : str
        The operation to perform:  'rad', 'add', 'sub', 'ext', 'ouo', 'del'
    size_amount : float
        The amount to over/undersize the shapes to be added/subtracted
    do_manh : bool
        True to perform manhattanization during the 'rad' operation

    Returns
    -------
    polygons_out : Union[gdspy.Polygon, gdspy.PolygonSet]
        The new polygons present on the output layer
    """
    # TODO: clean up the input polygons first ?

    # TODO: properly get the grid size from a tech file
    grid_size = global_grid_size

    # If there are no shapes to operate on, return the shapes currently on the output layer
    if polygon2 is None:
        return polygon1
    else:
        if operation == 'rad':
            # TODO: manh ?
            polygon_rough = dataprep_roughsize_gdspy(polygon2, size_amount=size_amount, do_manh=do_manh)

            buffer_size = max(size_amount - 2 * global_rough_grid_size, 0)
            polygon_rough_sized = dataprep_oversize_gdspy(polygon_rough, buffer_size)

            if polygon1 is None:
                polygon_out = polygon_rough_sized
            else:
                polygon_out = gdspy.fast_boolean(polygon1, polygon_rough_sized, 'or')
                polygon_out = gdspy.offset(polygon_out, 0, max_points=4094, join_first=True)

        elif operation == 'add':
            if polygon1 is None:
                polygon_out = dataprep_oversize_gdspy(polygon2, size_amount)
            else:
                polygon_out = gdspy.fast_boolean(polygon1, dataprep_oversize_gdspy(polygon2, size_amount), 'or')
                polygon_out = gdspy.offset(polygon_out, 0, max_points=4094, join_first=True)

        elif operation == 'sub':
            if polygon1 is None:
                polygon_out = None
            else:
                # TODO: Over or undersize the subtracted poly
                polygon_out = gdspy.fast_boolean(polygon1, dataprep_oversize_gdspy(polygon2, size_amount), 'not')
                polygon_out = gdspy.offset(polygon_out, 0, max_points=4094, join_first=True)

        elif operation == 'ext':
            # TODO:
            # if (not (member(LppOut, NotToExtendOrOverUnderOrUnderOverLpps) != nil)):
            if True:
                polygon_toextend = polygon1
                polygon_ref = polygon2
                polygon_out = polyop_extend(polygon_toextend, polygon_ref, size_amount)
            else:
                pass

        elif operation == 'ouo':
            # TODO
            # if (not (member(LppIn NotToExtendOrOverUnderOrUnderOverLpps) != nil)):
            if True:
                min_width = global_min_width
                min_space = global_min_width

                underofover_size = grid_size * ceil(0.5 * min_space / grid_size)
                overofunder_size = grid_size * ceil(0.5 * min_width / grid_size)
                polygon_o = dataprep_oversize_gdspy(polygon2, underofover_size)
                polygon_ou = dataprep_undersize_gdspy(polygon_o, underofover_size)
                polygon_ouu = dataprep_undersize_gdspy(polygon_ou, overofunder_size)
                polygon_out = dataprep_oversize_gdspy(polygon_ouu, overofunder_size)

            else:
                pass

        elif operation == 'del':
            # TODO
            polygon_out = None
            pass

        return polygon_out