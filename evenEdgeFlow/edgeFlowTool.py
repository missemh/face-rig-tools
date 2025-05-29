import maya.cmds as cmds

def run_edge_flow_on_selection(repeat_count=3):
    sel_edges = cmds.ls(selection=True, fl=True)
    if not sel_edges:
        cmds.warning("No edges selected.")
        return

    for i in range(repeat_count):
        print(f"Iteration {i+1}/{repeat_count}")
        for edge in sel_edges:
            cmds.select(edge, r=True)
            try:
                cmds.polyEditEdgeFlow(adjustEdgeFlow=1)
            except:
                cmds.warning(f"Failed to apply edge flow on {edge}")

    cmds.select(sel_edges, r=True)
    print("Done.")

# Usage
run_edge_flow_on_selection()
