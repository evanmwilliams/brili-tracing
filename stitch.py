import argparse
import json
import sys


def stitch_trace(blocks, trace):
    for block in blocks:
        try:
            insert_idx = next(
                i for i, v in enumerate(block.instrs) if v.get("label") == "entry"
            )
            insert_idx += 1
            block.instrs.insert(insert_idx, {"op": "speculate"})
            for instr in trace:
                insert_idx += 1
                block.instrs.insert(insert_idx, instr)
            block.instrs.insert(insert_idx + 1, {"op": "commit"})
            block.instrs.insert(
                insert_idx + 2,
                {"args": [], "op": "ret"},
            )
            block.instrs.insert(insert_idx + 3, {"label": "failed"})
        except StopIteration:
            pass

    return blocks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(exit_on_error=True)
    parser.add_argument("-t", type=str, help="path to trace file")
    args = parser.parse_args()
    cli_flags = vars(args)

    program = json.load(sys.stdin)

    trace_file_path = cli_flags["t"]
    trace_instr_strs = []

    with open(trace_file_path) as file:
        trace_instr = json.load(file)

    trace_instr_map = {"main": trace_instr[0]}
    trace_instr_map["main"] = [
        i
        for i in trace_instr_map["main"]
        if i.get("op") != "br" and i.get("op") != "jmp"
    ]

    for func in program["functions"]:
        if func.get("name") == "main":
            blocks = to_cfg(func["instrs"], 0)

            # operate on blocks
            stitch_trace(blocks, trace_instr_map["main"])

            func["instrs"] = blocks_to_instrs(blocks)

    json.dump(program, sys.stdout, indent=2)
