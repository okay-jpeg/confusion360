import traceback
import adsk.core
import adsk.fusion
import math

app = adsk.core.Application.get()
ui  = app.userInterface
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent
params = design.userParameters

def create_parameter(name: str, value_mm: float):
    """Create or update a user parameter (value in mm)"""
    expr = f'{value_mm} mm'
    
    param = params.itemByName(name)
    if param:
        param.expression = expr
    else:
        val = adsk.core.ValueInput.createByString(expr)
        param = params.add(name, val, 'mm', '')
    
    return param

def delete_parameters():
    x = params.itemByName('STOCK_X')
    if (x):
        params.itemByName('STOCK_X').deleteMe()
    y = params.itemByName('STOCK_Y')
    if (y):
        params.itemByName('STOCK_Y').deleteMe()
    z = params.itemByName('STOCK_Z')
    if (z):
        params.itemByName('STOCK_Z').deleteMe()

def delete_stock():
    occ = None
    for o in root.allOccurrences:
        if o.component.name == "STOCK":
            occ = o
            occ.deleteMe()
            break

def create_stock():

    delete_parameters()
    delete_stock()

    occ = next((o for o in root.allOccurrences if o.component.name == "PART" or o.component.name == "part"), None)
    if not occ:
        ui.messageBox("PART component not found!")
        return

    bbox = occ.boundingBox
    part_mm_x = round((bbox.maxPoint.x - bbox.minPoint.x) * 10)
    part_mm_y = round((bbox.maxPoint.y - bbox.minPoint.y) * 10)
    part_mm_z = round((bbox.maxPoint.z - bbox.minPoint.z) * 10)


    stock_mm_x = math.ceil(part_mm_x / 5) * 5 + 5
    stock_mm_y = math.ceil(part_mm_y / 5) * 5 + 5
    stock_mm_z = math.ceil((part_mm_z + 4) / 5) * 5                   

    # Create parameters and keep references
    px = create_parameter('STOCK_X', stock_mm_x)
    py = create_parameter('STOCK_Y', stock_mm_y)
    pz = create_parameter('STOCK_Z', stock_mm_z)

    # === Create STOCK component ===
    transform = adsk.core.Matrix3D.create()
    occ_stock = root.occurrences.addNewComponent(transform)
    stock_comp = occ_stock.component
    stock_comp.name = "STOCK"
    stock_comp.opacity = 0.3

    # Sketch
    sketch = stock_comp.sketches.add(stock_comp.xYConstructionPlane)
    lines = sketch.sketchCurves.sketchLines

    p1 = adsk.core.Point3D.create(0, 0, 0)
    p2 = adsk.core.Point3D.create(1, 1, 0)   # dummy size
    rectangle = lines.addTwoPointRectangle(p1, p2)

    # Link dimensions to parameters
    dims = sketch.sketchDimensions

    # X dimension
    dim_x = dims.addDistanceDimension(
        rectangle.item(0).startSketchPoint,
        rectangle.item(1).startSketchPoint,
        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        adsk.core.Point3D.create(stock_mm_x/20, -2, 0)
    )
    dim_x.parameter.expression = px.name

    # Y dimension
    dim_y = dims.addDistanceDimension(
        rectangle.item(0).startSketchPoint,
        rectangle.item(3).startSketchPoint,
        adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
        adsk.core.Point3D.create(-2, stock_mm_y/20, 0)
    )
    dim_y.parameter.expression = py.name

    # Extrude linked to parameter
    profile = sketch.profiles.item(0)
    extrudes = stock_comp.features.extrudeFeatures
    
    ext_input = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByString(pz.name))
    
    extrudes.add(ext_input)

def run(_context: str):
    try:
        create_stock()

    except:
        ui.messageBox(f'Failed:\n{traceback.format_exc()}')
