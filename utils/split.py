#!/usr/bin/env python
"""
Use this script to split a .mae[gz] trajectory file of N snapshots into N
separate receptor and N separate ligand .mae[gz] files.  You can also supply a
list of specific snapshot indices (1-based indexing) in a list or file (1 index
per line) to only output specific frames from the trajectory.  Can take custom
ligand and receptor output formats.

Run with
    $SCHRODINGER/run split.py infile1.maegz [infile2.maegz ...]
      [--snapshots snapshot_file]
      [--lig-fmt "${jobname}-%%d_lig.maegz"]
      [--rcp-fmt "${jobname}-%%d_rcp.maegz"]

You can specify multiple input files.  However, if you want to use specific
snapshots, then you can only do it one input file at a time.

Adapted from similar script by Peng He.

Author: Bill Flynn (wflynny@gmail.com)
Date: 3/30/2015
"""
import os
import re
import sys
import glob
import argparse
from schrodinger import structure, structureutil

def read_snapshot_indices(snapshot_str):
    # probably a list:
    if ' ' in snapshot_str:
        try:
            indices = [i-1 for i in map(int, snapshot_str.split(' '))]
        except Exception as e:
            print "Cannot parse snapshot list: %s"%snapshot_str
            print e.message, e.args
            sys.exit(1)
    # assume file
    else:
        if not os.path.exists(snapshot_str):
            print "Snapshot file doesn't exist: %s"%snapshot_str
            sys.exit(1)
        with open(snapshot_str, 'r') as fin:
            try:
                indices = [int(line.strip())-1 for line in fin.readlines()]
            except:
                print "Error reading snapshot file: %s"%snapshot_str
                sys.exit(1)
    return sorted(indices)

def quit(msg, args):
    print msg % args
    sys.exit(1)

def load_structure_reader(filepath):
    if not os.path.exists(filepath):
        quit("File %s doesn't exist!", filepath)

    basename, ext = os.path.splitext(filepath)
    if ext not in ('.mae', '.maegz'):
        quit("Extension %s from file %s not recognized.\nInput should "
             "be a Maestro-formatted .mae or .maegz file", (ext, filepath))

    try:
        reader = structure.StructureReader(filepath)
    except Exception as e:
        quit("Cannot open Maestro structure file %s\n. %s: %s",
             (filepath, e.message, e.args))

    return reader

def parse_arguments():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('infile', type=str, nargs='+', help='Input file(s)')
    parser.add_argument('--snapshots', type=str,
                        help='File containing or list of snapshot indices (1-based indexing)')
    parser.add_argument('--lig-fmt', type=str,
                        help='Ligand output file format.  Ex: "${jobname}-%%d_lig.maegz"')
    parser.add_argument('--rcp-fmt', type=str,
                        help='Receptor output file format.  Ex: "${jobname}-%%d_lig.maegz"')
    parser.add_argument('--rcp-asl', default='mol.num 1',
                        help='ASL string for the receptor. Default: "mol.num 1"')
    parser.add_argument('--lig-asl', default='mol.num 2',
                        help='ASL string for the ligand. Default: "mol.num 2"')

    return parser.parse_args()

def main():
    args = parse_arguments()

    file_list = []
    for item in args.infile:
        if '*' in item:
            file_list += list(glob.glob(item))
        else:
            file_list.append(item)

    if args.snapshots:
        snapshot_indices = read_snapshot_indices(args.snapshots)
        assert len(file_list) == 1, ("Should only run 1 file at a time with "
                                     "particular snapshots specified!")
    else:
        snapshot_indices = None

    for mae_file in file_list:
        s = load_structure_reader(mae_file)

        lig_out = '%d_lig.maegz'
        rcp_out = '%d_rcp.maegz'
        if args.lig_fmt:
            assert re.search(r'.*%d.*\.maegz', args.lig_fmt)
            lig_out = args.lig_fmt
        if args.rcp_fmt:
            assert re.search(r'.*%d.*\.maegz', args.rcp_fmt)
            rcp_out = args.rcp_fmt

        rcp_asl = args.rcp_asl
        lig_asl = args.lig_asl

        j = 1
        for i, lig_st in enumerate(s):
            if snapshot_indices and i not in snapshot_indices:
                continue

            rcp_st = lig_st.copy()

            lig_trj = lig_out%j
            rcp_trj = rcp_out%j

            # Select and delete lig from rcp structure
            lig_selection = structureutil.evaluate_asl(rcp_st, lig_asl)
            rcp_st.deleteAtoms(lig_selection)
            rcp_st.append(rcp_trj)

            # Select and delete rcp from lig structure
            rcp_selection = structureutil.evaluate_asl(lig_st, rcp_asl)
            lig_st.deleteAtoms(rcp_selection)
            lig_st.append(lig_trj)

            j += 1


if __name__ == "__main__":
    main()
