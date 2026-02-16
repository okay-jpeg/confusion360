import traceback
import adsk.core
import adsk.fusion
import adsk.cam
import re

app = adsk.core.Application.get()
ui  = app.userInterface
doc = app.activeDocument
cam = adsk.cam.CAM.cast(doc.products.itemByProductType('CAMProductType'))
text_palette = ui.palettes.itemById("TextCommands")

regular_setups = []
other_setups = []
fixture_setups = []
setup_pattern = r'^OP\d+\s(ALU|POM|AISI|STEEL|COPPER|ERTALYTE)(\sG\d+)?$'
tolerance_pattern = r'^\d+\.?\d*[a-zA-Z]\d+$'
fixtures_pattern = r'(FXT|JAWS)'

#TIME IN SECONDS.

#setup time
MANUAL_TOOL_CHANGE_TIME = 300
INITIAL_SETUP = 1200

#unit time
CONSECUTIVE_SETUP = 300
MEASURING_TIME = 420
STANDARD_QC = 300
T_FIXTURE = 600

FINE_TOLERANCES = False
FUCKERY_COEFF = 1.0

NUMBER_OF_PASSES = 7

def time_human_readable(machining_seconds):
    seconds = machining_seconds % 60
    seconds_rem = machining_seconds // 60
    minutes = seconds_rem % 60
    minutes_rem = seconds_rem // 60
    hours = minutes_rem % 60
    hours_rem = minutes_rem // 60
    nice_time = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    return nice_time


def run(_context: str):
    global FINE_TOLERANCES, FUCKERY_COEFF

    total_machining_time = 0
    time_spent_on_tolerances = 0
    tool_change_time = 0
    setup_time = INITIAL_SETUP
    tool_changes = 0
    tolerances_cycle_time = 0
    tolerances_list = []
    tool_list = []
    setups_with_fixture = 0
   

    try:
        text_palette.writeText(f"")
        text_palette.writeText(f"------------------------------------------------")
        for setup in cam.setups:
            if re.search(setup_pattern, setup.name):
                regular_setups.append(setup)
            elif re.search(fixtures_pattern, setup.name):
                fixture_setups.append(setup)
            else:
                other_setups.append(setup)
                   
        for setup_count, setup in enumerate(regular_setups):
            text_palette.writeText(f"{setup.name}")

            if re.search(r'FINE_TOLERANCES', setup.notes):
                FINE_TOLERANCES = True
                FUCKERY_COEFF = 1.5

            if re.search(r'FIXTURE_SETUPS', setup.notes):
                setups_with_fixture = int(re.findall(r'\d+', setup.notes)[0])

            for op in setup.operations:
                try:
                    tool = op.tool
                    tool_number = tool.parameters.itemByName('tool_number').value.value
                    op_name = op.name
                    tool_description = tool.description

                    if tool_number > 23 and tool_number != 30:
                        if tool_description not in tool_list:
                            text_palette.writeText(f"----{tool_description}")
                            tool_list.append(tool_description)
                except:
                    pass

                if re.search(tolerance_pattern, op_name):
                    tolerances_list.append(op_name)
                    tolerances_cycle_time += cam.getMachiningTime(op, 0,0,0).machiningTime * NUMBER_OF_PASSES

            if setup_count >= 0:
                total_machining_time += CONSECUTIVE_SETUP

            machine_seconds = cam.getMachiningTime(setup, 0, 0, 0).machiningTime
            total_machining_time += machine_seconds

        for tool in tool_list:
            tool_changes += 1
            tool_change_time += MANUAL_TOOL_CHANGE_TIME

        #if fixture_setups:
        #    total_machining_time += T_FIXTURE

        # if tolerances are found, we measure each time we make a slight adjustment.
        if tolerances_list:
            time_spent_on_tolerances += MEASURING_TIME
        else:
            time_spent_on_tolerances += STANDARD_QC

        total_machining_time += tolerances_cycle_time
        #total_machining_time += tool_change_time
        total_machining_time += time_spent_on_tolerances
        total_machining_time *= FUCKERY_COEFF
        total_machining_time += T_FIXTURE * setups_with_fixture

        setup_time += tool_change_time

        text_palette.writeText(f"")
        if FINE_TOLERANCES:
            text_palette.writeText(f"Fine tolerances detected")
            text_palette.writeText(f"---FUCKERY COEFFICIENT: {FUCKERY_COEFF}")

        text_palette.writeText(f"Setup time: {setup_time // 60} minutes")
        if setups_with_fixture:
            text_palette.writeText(f"Setups requiring fixturing: {setups_with_fixture}")

        text_palette.writeText(f"Manual tool changes: {tool_changes}")
        if setups_with_fixture:
            text_palette.writeText(f"Fixture needed")
        text_palette.writeText(f"Estimated time on tool changes: {tool_change_time // 60} minutes")
        text_palette.writeText(f"Tolerances found: {tolerances_list}")
        text_palette.writeText(f"Machining time: {time_human_readable(total_machining_time)}")
        text_palette.writeText(f"------------------------------------------------")

    except Exception as e:  
        ui.messageBox(f"{e}")
